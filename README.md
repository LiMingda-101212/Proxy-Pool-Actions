# 🌐 ProxyPool

`代理池管理项目`

## 🎯总述:

### 项目结构

本项目包含两部分,分别为`开发者本地一份完全版代码`和`云端公开仓库的actions自动管理代码`

```
ProxyPool

├── <云端 Github Actions> Proxy-Pool-Actions/
│      ├── actions_main.py
│      ├── proxies.csv
│      ├── README.md
│      ├── data/
│      │      └── config.json
│      └── .github/workflows/
│                      ├── Crawl-and-verify-new-proxies.yml
│                      └── Update-existing-proxies.yml
│
└── <开发者本地 Local> ProxyPool/
        ├── main.py                    # 主入口
        │
        ├── core/                      # 核心模块
        │   ├── __init__.py
        │   ├── config.py             # 配置读取/保存
        │   └── menu.py               # 主菜单
        │
        ├── collectors/               # 采集层
        │   ├── __init__.py
        │   ├── web_crawler.py       # 网页爬虫
        │   └── file_loader.py       # 文件加载
        │
        ├── validators/               # 验证层
        │   ├── __init__.py
        │   ├── base_validator.py    # 基础验证
        │   ├── browser_validator.py # 浏览器验证
        │   └── security_checker.py  # 安全验证
        │
        ├── schedulers/               # 调度层
        │   ├── __init__.py
        │   ├── manual_scheduler.py  # 手动调度
        │   ├── api_server.py        # API服务
        │   └── pool_monitor.py      # 代理池状态监控
        │
        ├── storage/                  # 存储层
        │   ├── __init__.py
        │   └── database.py          # 数据库操作
        │
        ├── sync/                     # 同步层
        │   ├── __init__.py
        │   └── github_sync.py       # GitHub同步
        │
        ├── utils/                    # 工具函数
        │   ├── __init__.py
        │   ├── helpers.py           # 通用工具
        │   ├── change_configs.py     # 修改设置
        │   ├── playwright_check.py    # 检查playwright安装
        │   ├── signal_manager.py     # 信号处理
        │   ├── use_api.py            # api使用
        │   └── interrupt_handler.py # 中断处理
        │
        ├── data/                     # 数据文件
        │   ├── config.json          # 配置文件
        │   ├── settings.py          # 数据存储
        │   └── web/                 # 网页文件
        │       └── index.html
        │
        └── interrupt/               # 中断记录目录
            └── *.csv
```

### 备注

爬虫部分仅供学习参考使用

## 🎯云端代码 (actions_main.py)

`github actions代理自动管理`

负责与开发者本地代理池对接,由于actions耗时长,所以放在一个[公开仓库<点这里查看>](https://github.com/LiMingda-101212/Proxy-Pool-Actions)内

### Workflows工作流

1. 爬取并验证新代理,每天北京时间10-12点运行 - UTC+2
2. 重新验证已有代理,每天北京时间13-15点运行 - UTC+5

### Actions当前状态

爬取并验证新代理
![Proxy Pool Update](https://github.com/LiMingda-101212/Proxy-Pool-Actions/actions/workflows/Crawl-and-verify-new-proxies.yml/badge.svg)

重新验证已有代理
![Proxy Pool Update](https://github.com/LiMingda-101212/Proxy-Pool-Actions/actions/workflows/Update-existing-proxies.yml/badge.svg)


## 🎯开发者本地主代码 (main.py)

`代理自动管理`

实现较为全面的功能:
- 1 .加载和验证新代理,可从爬虫(自动爬取,根据情况指定类型),本地文件(用于手动添加代理时使用,可以选择代理类型(这样比较快),也可用自动检测(若用自动检测可能较慢))加载,并将通过的代理添加到代理池.新代理使用自动检测类型或指定类型.在验证之前会先将重复代理,错误代理筛除(集合筛选),确保不做无用功.满分100分,新代理只要通过`百度`或`Google`任一验证就98分,错误代理和无效代理0分.支持透明代理检测功能，识别会泄露真实IP的代理.有中断恢复功能,当验证过程被中断时,会自动保存已完成的代理到代理池,未完成的代理保存到中断文件,下次可选择继续验证可以获取代理信息(城市,运营商等),对于已经有ip信息的代理不重复进行获取信息
- 2 .检验和更新代理池内代理的有效性,使用代理池文件中保存的上次结果类型作为验证使用类型,验证是否支持国内和国外,再次验证成功一个(国内/国外)加1分,全成功加2分,无效代理和错误代理减1分,更直观的分辨代理的稳定性.支持透明代理检测功能，识别会泄露真实IP的代理.
- 3 .浏览器使用验证,部分代理没法在浏览器中使用(安全问题),用`playwright`检测出浏览器可用代理.
- 4 .代理安全验证,检验代理安全性
- 5 .提取指定数量的代理,优先提取分数高,稳定的代理,可指定提取类型,支持范围,是否为透明代理,浏览器是否可用
- 6 .查看代理池状态(总代理数量,各种类型代理的分数分布情况,支持范围,浏览器是否可用统计)
- 7 .与部署在github上由actions自动维护的代理池合并,将github精简格式转为本地全面格式
- 8 .API服务,提供开启和调试功能.为了防止一个代理在不同爬虫被多次使用,使用了代理状态,未调用时`idle`,调用获取会使状态变为`busy`,失败会变为`dead`并很快会被清理.
- 9 .设置菜单,不用每次手动改`config.json`文件
- 10.帮助菜单,,提供帮助信息

## 🎯代理池

云端代理池文件(proxies.csv)介绍(存储基本信息,云端便携版)：

```
类型,代理,分数,是否支持中国,是否支持国际,是否为透明代理,检测到的IP
Type,Proxy:Port,Score,China,International,Transparent,DetectedIP

💭详细介绍:
Type -> 类型,支持http/socks
Proxy:Port -> 代理:端口(Proxy:Port)
Score -> 积分,0-100,直观反映代理稳定性
China -> 是否支持中国,True/False,使用中国的网站验证(现在用的Baidu)
International -> 是否支持国际,True/False,使用国际的网站验证(现在用的Google)
Transparent -> 是否为透明代理,True/False,与本机ip进行对比
DetectedIP -> 检测到的IP,unknown/ip/dict,有的可能很详细
```

开发者本地代理池数据库(SQLite:proxies.db)介绍(各种信息全面)：
```
proxies 代理数据表:
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proxy TEXT UNIQUE NOT NULL,
        score INTEGER DEFAULT 50,
        types TEXT,  -- JSON数组字符串 ["http", "socks5"]
        support_china BOOLEAN DEFAULT 0,
        support_international BOOLEAN DEFAULT 0,
        transparent BOOLEAN DEFAULT 0,
        detected_ip TEXT,
        city TEXT,
        region TEXT,
        country TEXT,
        loc TEXT,
        org TEXT,
        postal TEXT,
        timezone TEXT,
        browser_valid BOOLEAN DEFAULT 0,
        browser_check_date TEXT,
        browser_response_time REAL DEFAULT -1,
        dns_hijacking TEXT,
        ssl_valid TEXT,
        malicious_content TEXT,
        security_check_date TEXT,
        avg_response_time REAL DEFAULT 0,
        success_rate REAL DEFAULT 0.0,
        last_checked TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

proxy_status 代理状态表:
        proxy TEXT PRIMARY KEY,
        status TEXT DEFAULT 'idle',  -- idle, busy, dead
        task_id TEXT,
        acquire_time REAL,
        heartbeat_time REAL,
        FOREIGN KEY (proxy) REFERENCES proxies(proxy) ON DELETE CASCADE
        
proxy_usage 使用记录表:
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proxy TEXT,
        task_id TEXT,
        start_time REAL,
        end_time REAL,
        success BOOLEAN,
        response_time REAL,
        score_change INTEGER,
        FOREIGN KEY (proxy) REFERENCES proxies(proxy) ON DELETE CASCADE

```

## 更新

### (主代码 main.py )

```
2025-12-14 : ✅ 实现了:
    ✳️1.加载和验证新代理,可从爬虫(自动爬取,根据情况指定类型),本地文件(用于手动添加代理时使用,可以选择代理类型(这样比较快),
    也可用自动检测(若用自动检测可能较慢))加载,并将通过的代理添加到代理池文件.新代理使用自动检测类型或指定类型.
    在验证之前会先将重复代理,错误代理筛除(集合筛选),确保不做无用功.
    满分100分,新代理只要通过百度或Google任一验证就98分,错误代理和无效代理0分(会被0分清除函数清除).
    支持透明代理检测功能，识别会泄露真实IP的代理.
    有中断恢复功能,当验证过程被中断时,会自动保存已完成的代理到代理池,未完成的代理保存到中断文件,下次可选择继续验证
    可以获取代理信息(城市,运营商等),对于已经有ip信息的代理不重复进行获取信息
    ✳️2.检验和更新代理池内代理的有效性,使用代理池文件中的Type作为类型,
    验证是否支持国内和国外,再次验证成功一个(国内/国外)加1分,全成功加2分,无效代理和错误代理减1分,更直观的分辨代理的稳定性.
    支持透明代理检测功能，识别会泄露真实IP的代理.
    有中断恢复功能,当验证过程被中断时,会自动保存已完成的代理到代理池,未完成的代理保存到中断文件,下次可选择继续验证
    ✳️3.浏览器使用验证,用playwright检测出代理在真实浏览器环境中的可用性,有中断恢复功能可用代理
    ✳️4.🛠️代理安全验证,检验代理安全性,已经实现基本代码,主函数开发中 - 开发中
    ✳️5.提取指定数量的代理,优先提取分数高,稳定的代理,可指定提取类型,支持范围,是否为透明代理,浏览器是否可用
    ✳️6.查看代理池状态(总代理数量,各种类型代理的分数分布情况,支持范围,浏览器是否可用统计)
    ✳️7.与部署在github上由actions自动维护的代理池合并,将github精简格式转为本地全面格式
    ✳️8.设置菜单,不用每次手动改config.json文件
    ✳️9.帮助菜单,,提供帮助信息
    本版本主代码代理池格式: 代理,分数,代理信息dict
2025-12-20 : 将程序改为标准代理池,添加了api运行入口,开放多个url用于不同用途的调用.为了防止一个代理在不同爬虫被多次使用,使用了代理状态,未调用时"idle",调用获取会使状态变为"busy",失败会变为"dead"并很快会被清理.
2025-12-21 : 将代理池迁移到SQLite中,围绕数据库进行了改动
2025-01-11 : 将一个main文件分成多个模块,分别实现不同功能
```

### (云端 actions_main.py)

实现基本的爬取并验证和重新验证已有代理功能

```
2025-12-14 : ✅依照主代码编写,爬取验证 与 重新验证 被拆成两个Workflows
    云端代码格式: 类型,代理,分数,是否支持中国,是否支持国际,是否为透明代理,检测到的IP
```

