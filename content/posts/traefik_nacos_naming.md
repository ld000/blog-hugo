---
title: 为 Traefik 添加从 nacos 读取服务地址功能
date: 2021-06-12
tags: [""]
---

## 软件版本

Traefik 版本：2.4.0

## 背景

Traefik 是一个 go 实现的高性能 API 网关，本身支持多种配置加载方式，包括 file, k8s, consul 等。

我们之前用的file作为配置文件，路由配置文件中会配置应用的路由信息和应用的负载信息。一个服务的配置信息类似下面这样：

```yaml
http:
  services:
    dev-service:
      loadBalancer:
        servers:
        - url: http://aliyun-slb-service:8080
        passHostHeader: true
  routers:
    dev:
      entryPoints:
      - test
      service: dev-service
      rule: PathPrefix(`/path`)
```

服务的请求 url 配置的是服务前面挂载的负载均衡(用的阿里云的SLB)，服务上下线等会从SLB上注册反注册。这样所有对外的服务前面都需要挂载一层负载，增加了复杂度和调用链长度。更好的做法是网关能自动从注册中心拉取服务的地址列表，就不需要在服务上再挂载一个负载均衡了。

我们现在后端注册中心使用的是 nacos，Traefik 现版本是不支持 nacos 的，需要简单修改下源码，添加一个 nacos 的 provider。

## Consul provider

Traefik 虽然没有 nacos 的实现，但是有别的注册中心的实现，比如 consul。在新添加 provider 之前可以先看下 Traefik consul 是怎么实现的。

consul 逻辑是，服务信息会从注册的服务上直接读取，路由信息等配置都是tag信息，类似下图这样，需要每个配置字段都设定一个tag。

![https://void.oss-cn-beijing.aliyuncs.com/img/20210714190352.jpg](https://void.oss-cn-beijing.aliyuncs.com/img/20210714190352.jpg)

(图从网上随便搜的)

这样的话每个服务都需要在consul中注册很多的tag，使用起来不太方便，也不方便维护和快速查找。

考虑到方便维护和兼容之前的文件配置，想要实现的效果是路由信息还是从文件中读取，服务地址信息从 nacos 中读取。之后与文件的配置文件合并，为了兼容之前的配置，文件中的服务信息也会读取，如果 nacos 中有重复的服务，就用 nacos 的覆盖文件的。

## 最终的配置文件

代码修改好后的配置文件就会像下面这样

### 静态配置里的 provider 配置

```yaml
providers:
  nacos:
    file:
      watch: true
      filename: "/Users/d/depend/config/route/test.yaml"
      debugLogGeneratedTemplate: true
    endpoint:
      host: devnacos.inc.com
      port: 8848
      group: aaa
      logDir: "/tmp/nacos/log"
      cacheDir: "/tmp/nacos/cache"
```

配置里有两部分：

- 第一部分是 file，这个和自带的 file provider 逻辑一样
- 第二部分是 endpoint，这个是 nacos SDK 的配置

### 路由配置

```yaml
http:
  routers:
    dev:
      entryPoints:
      - test
      service: nacos中的服务名
      rule: PathPrefix(`/path`)
      middlewares:
      - test-retry
  middlewares:
    test-retry:
      retry:
        attempts: 3
        initialInterval: 10ms
```

去掉了 services 配置，从 nacos 中读取，路由的 service 对应 nacos 中的服务名。

> 这里加的retry插件主要是用来failover的，服务短时不可用可以故障转移，请求下个服务实例（比如服务下线时网关还未接到下线通知，请求了已下线服务）

## 代码实现

接下来看下代码实现，需要为 Traefik 添加一个叫 nacos 的 provider。

### 主逻辑

首先在 `pkg/provider` 下添加一个文件夹 nacos，在里面添加个 nacos.go 文件，主要逻辑都会在这个文件里实现。

首先添加从文件读取配置的代码，这里大部分代码都可以复用 Traefik 自带的文件解析 provider

```go
// 把文件解析成配置，复用 Traefik 原有代码
fileProvider := file.Provider{
	Directory: p.File.Directory,
	Watch: p.File.Watch,
	Filename: p.File.Filename,
	DebugLogGeneratedTemplate: p.File.DebugLogGeneratedTemplate,
}

fileConfiguration, err := fileProvider.BuildConfiguration()

// 注册文件变化监听，因为监听回调逻辑不一样，这里自己实现下
if p.File.Watch {
	var watchItem string

	switch {
	case len(p.File.Directory) > 0:
		watchItem = p.File.Directory
	case len(p.File.Filename) > 0:
		watchItem = filepath.Dir(p.File.Filename)
	default:
		return nil, errors.New("error using file configuration provider, neither filename or directory defined")
	}

	if err := p.addWatcher(pool, watchItem, configurationChan, p.watcherCallback); err != nil {
		return nil, err
	}
}
```

回调的代码省略，见下面的完整代码。

然后添加 nacos 的代码。

先安装 SDK

```bash
go get -u github.com/nacos-group/nacos-sdk-go
```

和 nacos 的交互主要是获取实例信息和注册服务变化监听。

```go
// 首先初始化 nacos 实例
p.client, err = createClient(p.EndPoint)

// 获取需要的服务，循环获取地址。我这里简化了，获取了所有服务
services, err := p.fetchServices()
for _, service := range services {
		instances, err := p.client.SelectAllInstances(vo.SelectAllInstancesParam{
			ServiceName: service,
			GroupName:   p.EndPoint.Group,
			//HealthyOnly: true,
		})

		// ...

		// 注册服务变化的监听
		err = p.client.Subscribe(&vo.SubscribeParam{
			ServiceName: service,
			GroupName:   p.EndPoint.Group,
			SubscribeCallback: func(services []model.SubscribeService, err error) {
				p.nacosCallback(&services, configurationChan)
			},
		})
		
		// ...
}
```

之后还需要注册个定时任务，来定时拉取最新的服务状态，做个兜底。

```go
pool.GoCtx(func(routineCtx context.Context) {
		ctxLog := log.With(routineCtx, log.Str(log.ProviderName, "nacos"))
		logger := log.FromContext(ctxLog)

		operation := func() error {
			ticker := time.NewTicker(15 * time.Second)

			for {
				select {
				case <-ticker.C:
					_, err = p.nacosProvide(configurationChan)
					if err != nil {
						logger.Errorf("error get nacos service data, %v", err)
						return err
					}
					configuration := p.buildConfiguration()
					sendConfigToChannel(configurationChan, configuration)
				case <-routineCtx.Done():
					ticker.Stop()
					return nil
				}
			}
		}

		notify := func(err error, time time.Duration) {
			logger.Errorf("Provider connection error %+v, retrying in %s", err, time)
		}

		err := backoff.RetryNotify(safe.OperationWithRecover(operation), backoff.WithContext(job.NewBackOff(backoff.NewExponentialBackOff()), ctxLog), notify)
		if err != nil {
			logger.Errorf("Cannot connect to nacos server %+v", err)
		}
})
```

最终的 nacos 文件

```go
package nacos

import (
	"context"
	"errors"
	"fmt"
	"github.com/cenkalti/backoff/v4"
	"github.com/nacos-group/nacos-sdk-go/clients"
	"github.com/nacos-group/nacos-sdk-go/clients/naming_client"
	"github.com/nacos-group/nacos-sdk-go/common/constant"
	"github.com/nacos-group/nacos-sdk-go/common/logger"
	"github.com/nacos-group/nacos-sdk-go/model"
	"github.com/nacos-group/nacos-sdk-go/vo"
	"github.com/traefik/traefik/v2/pkg/config/dynamic"
	"github.com/traefik/traefik/v2/pkg/job"
	"github.com/traefik/traefik/v2/pkg/log"
	"github.com/traefik/traefik/v2/pkg/provider/file"
	"github.com/traefik/traefik/v2/pkg/safe"
	"gopkg.in/fsnotify.v1"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

type Provider struct {
	File *FileConfig `description:"Nacos file settings" json:"file,omitempty" toml:"file,omitempty" yaml:"file,omitempty" export:"true"`
	EndPoint *EndpointConfig `description:"Nacos endpoint settings" json:"endpoint,omitempty" toml:"endpoint,omitempty" yaml:"endpoint,omitempty" export:"true"`

	client naming_client.INamingClient
	fileConfig *dynamic.Configuration
	nacosServices *map[string]*dynamic.Service
}

type FileConfig struct {
	Directory                 string `description:"Load dynamic configuration from one or more .toml or .yml files in a directory." json:"directory,omitempty" toml:"directory,omitempty" yaml:"directory,omitempty" export:"true"`
	Watch                     bool   `description:"Watch provider." json:"watch,omitempty" toml:"watch,omitempty" yaml:"watch,omitempty" export:"true"`
	Filename                  string `description:"Load dynamic configuration from a file." json:"filename,omitempty" toml:"filename,omitempty" yaml:"filename,omitempty" export:"true"`
	DebugLogGeneratedTemplate bool   `description:"Enable debug logging of generated configuration template." json:"debugLogGeneratedTemplate,omitempty" toml:"debugLogGeneratedTemplate,omitempty" yaml:"debugLogGeneratedTemplate,omitempty" export:"true"`
}

type EndpointConfig struct {
	Host          string                  `description:"The host of the Nacos server" json:"host,omitempty" toml:"host,omitempty" yaml:"host,omitempty" export:"true"`
	Port          uint64                  `description:"The port of the Nacos server" json:"port,omitempty" toml:"port,omitempty" yaml:"port,omitempty" export:"true"`
	Group         string                  `description:"The group of the Nacos server" json:"group,omitempty" toml:"group,omitempty" yaml:"group,omitempty" export:"true"`
	LogDir         string                  `description:"The logDir of the Nacos server" json:"logDir,omitempty" toml:"logDir,omitempty" yaml:"logDir,omitempty" export:"true"`
	CacheDir         string                `description:"The cacheDir of the Nacos server" json:"cacheDir,omitempty" toml:"cacheDir,omitempty" yaml:"cacheDir,omitempty" export:"true"`
}

func (p *Provider) Init() error {
	return nil
}

func (p *Provider) Provide(configurationChan chan<- dynamic.Message, pool *safe.Pool) error {
	//logger := log.WithoutContext().WithField(log.ProviderName, "nacos")

	_, err := p.fileProvide(configurationChan, pool)
	if err != nil {
		return err
	}

	p.client, err = createClient(p.EndPoint)
	if err != nil {
		return fmt.Errorf("error create nacos client, %w", err)
	}

	_, err = p.nacosProvide(configurationChan)
	if err != nil {
		return err
	}
	configuration := p.buildConfiguration()
	sendConfigToChannel(configurationChan, configuration)

	pool.GoCtx(func(routineCtx context.Context) {
		ctxLog := log.With(routineCtx, log.Str(log.ProviderName, "nacos"))
		logger := log.FromContext(ctxLog)

		operation := func() error {
			ticker := time.NewTicker(15 * time.Second)

			for {
				select {
				case <-ticker.C:
					_, err = p.nacosProvide(configurationChan)
					if err != nil {
						logger.Errorf("error get nacos service data, %v", err)
						return err
					}
					configuration := p.buildConfiguration()
					sendConfigToChannel(configurationChan, configuration)
				case <-routineCtx.Done():
					ticker.Stop()
					return nil
				}
			}
		}

		notify := func(err error, time time.Duration) {
			logger.Errorf("Provider connection error %+v, retrying in %s", err, time)
		}

		err := backoff.RetryNotify(safe.OperationWithRecover(operation), backoff.WithContext(job.NewBackOff(backoff.NewExponentialBackOff()), ctxLog), notify)
		if err != nil {
			logger.Errorf("Cannot connect to nacos server %+v", err)
		}
	})

	return nil
}

func (p *Provider) buildConfiguration() *dynamic.Configuration {
	config := p.fileConfig
	for k, v := range *p.nacosServices {
		config.HTTP.Services[k] = v
	}

	return config
}

func (p *Provider) nacosProvide(configurationChan chan<- dynamic.Message) (*map[string]*dynamic.Service, error) {
	services, err := p.fetchServices()
	if err != nil {
		return nil, err
	}

	serviceMap := make(map[string]*dynamic.Service)
	for _, service := range services {
		instances, err := p.client.SelectAllInstances(vo.SelectAllInstancesParam{
			ServiceName: service,
			GroupName:   p.EndPoint.Group,
			//HealthyOnly: true,
		})

		if err != nil {
			logger.Errorf("Skip item %s: %v", service, err)
			continue
		}
		
		err = p.client.Subscribe(&vo.SubscribeParam{
			ServiceName: service,
			GroupName:   p.EndPoint.Group,
			SubscribeCallback: func(services []model.SubscribeService, err error) {
				p.nacosCallback(&services, configurationChan)
			},
		})

		if err != nil {
			logger.Errorf("Skip item %s: %v", service, err)
			return nil, err
		}

		var servers []dynamic.Server
		for _, instance := range instances {
			server := dynamic.Server{
				URL: "http://" + instance.Ip + ":" + strconv.FormatUint(instance.Port, 10),
			}
			servers = append(servers, server)
		}

		b := true
		serviceMap[service] = &dynamic.Service{
			LoadBalancer: &dynamic.ServersLoadBalancer{
				Sticky:             nil,
				Servers:            servers,
				HealthCheck:        nil,
				PassHostHeader:     &b,
				ResponseForwarding: nil,
			},
		}
	}

	p.nacosServices = &serviceMap

	return &serviceMap, nil
}

func (p *Provider) nacosCallback(services *[]model.SubscribeService, configurationChan chan<- dynamic.Message) {
	serviceSet := make(map[string]bool)
	for _, service := range *services {
		nameSplit := strings.Split(service.ServiceName, "@")
		serviceName := nameSplit[2]

		serviceSet[serviceName] = true
	}

	for s := range serviceSet {
		nacosServices := *p.nacosServices
		serviceName := s

		instances, err := p.client.SelectInstances(vo.SelectInstancesParam{
			ServiceName: serviceName,
			GroupName:   p.EndPoint.Group,
			HealthyOnly: true,
		})

		if err != nil {
			logger.Errorf("Skip item %s: %v", s, err)
			continue
		}

		var servers []dynamic.Server
		for _, instance := range instances {
			server := dynamic.Server{
				URL: "http://" + instance.Ip + ":" + strconv.FormatUint(instance.Port, 10),
			}
			servers = append(servers, server)
		}

		serviceLB := nacosServices[serviceName]
		if serviceLB == nil {
			b := true
			nacosServices[serviceName] = &dynamic.Service{
				LoadBalancer: &dynamic.ServersLoadBalancer{
					Sticky:             nil,
					Servers:            servers,
					HealthCheck:        nil,
					PassHostHeader:     &b,
					ResponseForwarding: nil,
				},
			}
		} else {
			nacosServices[serviceName].LoadBalancer.Servers = servers
		}
	}

	configuration := p.buildConfiguration()
	sendConfigToChannel(configurationChan, configuration)
}

func (p *Provider) fileProvide(configurationChan chan<- dynamic.Message, pool *safe.Pool) (*dynamic.Configuration, error) {
	fileProvider := file.Provider{
		Directory: p.File.Directory,
		Watch: p.File.Watch,
		Filename: p.File.Filename,
		DebugLogGeneratedTemplate: p.File.DebugLogGeneratedTemplate,
	}

	fileConfiguration, err := fileProvider.BuildConfiguration()
	if err != nil {
		return nil, err
	}
	//fileConfiguration.HTTP.Services = make(map[string]*dynamic.Service)
	//fileConfiguration.TCP.Services = make(map[string]*dynamic.TCPService)
	//fileConfiguration.UDP.Services = make(map[string]*dynamic.UDPService)
	p.fileConfig = fileConfiguration

	if p.File.Watch {
		var watchItem string

		switch {
		case len(p.File.Directory) > 0:
			watchItem = p.File.Directory
		case len(p.File.Filename) > 0:
			watchItem = filepath.Dir(p.File.Filename)
		default:
			return nil, errors.New("error using file configuration provider, neither filename or directory defined")
		}

		if err := p.addWatcher(pool, watchItem, configurationChan, p.watcherCallback); err != nil {
			return nil, err
		}
	}

	return fileConfiguration, nil
}

func (p *Provider) addWatcher(pool *safe.Pool, directory string, configurationChan chan<- dynamic.Message, callback func(chan<- dynamic.Message, fsnotify.Event)) error {
	watcher, err := fsnotify.NewWatcher()
	if err != nil {
		return fmt.Errorf("error creating file watcher: %w", err)
	}

	err = watcher.Add(directory)
	if err != nil {
		return fmt.Errorf("error adding file watcher: %w", err)
	}

	// Process events
	pool.GoCtx(func(ctx context.Context) {
		defer watcher.Close()
		for {
			select {
			case <-ctx.Done():
				return
			case evt := <-watcher.Events:
				if p.File.Directory == "" {
					_, evtFileName := filepath.Split(evt.Name)
					_, confFileName := filepath.Split(p.File.Filename)
					if evtFileName == confFileName {
						callback(configurationChan, evt)
					}
				} else {
					callback(configurationChan, evt)
				}
			case err := <-watcher.Errors:
				log.WithoutContext().WithField(log.ProviderName, "nacos").Errorf("Watcher event error: %s", err)
			}
		}
	})
	return nil
}

func (p *Provider) watcherCallback(configurationChan chan<- dynamic.Message, event fsnotify.Event) {
	watchItem := p.File.Filename
	if len(p.File.Directory) > 0 {
		watchItem = p.File.Directory
	}

	logger := log.WithoutContext().WithField(log.ProviderName, "nacos")

	if _, err := os.Stat(watchItem); err != nil {
		logger.Errorf("Unable to watch %s : %v", watchItem, err)
		return
	}

	fileProvider := file.Provider{
		Directory: p.File.Directory,
		Watch: p.File.Watch,
		Filename: p.File.Filename,
		DebugLogGeneratedTemplate: p.File.DebugLogGeneratedTemplate,
	}
	configuration, err := fileProvider.BuildConfiguration()
	if err != nil {
		logger.Errorf("Error occurred during watcher callback: %s", err)
		return
	}

	p.fileConfig = configuration

	sendConfigToChannel(configurationChan, p.buildConfiguration())
}

func createClient(cfg *EndpointConfig) (naming_client.INamingClient, error) {
	// server
	sc := []constant.ServerConfig{
		*constant.NewServerConfig(cfg.Host, cfg.Port),
	}

	// client
	cc := *constant.NewClientConfig(
		//constant.WithNamespaceId("e525eafa-f7d7-4029-83d9-008937f9d468"),
		constant.WithTimeoutMs(5000),
		constant.WithNotLoadCacheAtStart(true),
		constant.WithLogDir(cfg.LogDir),
		constant.WithCacheDir(cfg.CacheDir),
		constant.WithRotateTime("1h"),
		constant.WithMaxAge(3),
		constant.WithLogLevel("info"),
	)

	namingClient, err := clients.NewNamingClient(
		vo.NacosClientParam{
			ClientConfig:  &cc,
			ServerConfigs: sc,
		},
	)

	if err != nil {
		panic(err)
	}

	return namingClient, nil
}

func (p *Provider) fetchServices() ([]string, error) {
	i := 1
	var filtered []string
	for {
		serviceInfos, err := p.client.GetAllServicesInfo(vo.GetAllServiceInfoParam{
			GroupName: p.EndPoint.Group,
			PageNo: uint32(i),
			PageSize:  100,
		})

		if err != nil {
			return nil, err
		}

		if serviceInfos.Count == 0 {
			break
		}

		for _, serviceInfo := range serviceInfos.Doms {
			filtered = append(filtered, serviceInfo)
		}

		i = i + 1
	}

	return filtered, nil
}

func sendConfigToChannel(configurationChan chan<- dynamic.Message, configuration *dynamic.Configuration) {
	configurationChan <- dynamic.Message{
		ProviderName:  "nacos",
		Configuration: configuration,
	}
}
```

### 配置解析

然后添加静态配置解析的代码

在`pkg/config/static/static_config.go` 里添加 nacos 配置结构体：

```go
type Providers struct {
// 省略原有代码

	Nacos     *nacos.Provider `description:"Enable Nacos backend with default settings." json:"nacos,omitempty" toml:"nacos,omitempty" yaml:"nacos,omitempty"`
}
```

在`pkg/provider/aggregator/aggregator.go` 里添加 nacos 初始化：

```go
func NewProviderAggregator(conf static.Providers) ProviderAggregator {
// 省略原有代码

	if conf.Nacos != nil {
		p.quietAddProvider(conf.Nacos)
	}

	return p
}
```

## 结尾

修改后 Traefik 就可以从注册中心自动拉取实例信息来负载了，方便了很多。上边的实例做了一些简化，比如从 nacos 获取了全量服务，在服务很多的情况下不太高效，可以只获取需要用的服务、路由信息修改可以放到配置中心或者修改下UI，就可以可视化操作了、等等。实际使用时可以根据自己的情况做下修改。