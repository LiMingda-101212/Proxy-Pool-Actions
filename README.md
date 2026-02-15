# 🌐 ProxyPool

---

## **注意:这是主代码的云端仓库,负责与主代码对接,以下内容为主代码说明**

`代理池管理项目`

一个功能全面的代理池管理系统，支持代理采集、验证、管理、安全检测和自动维护。

1. 总述
2. 快速开始
3. 代码介绍
4. 更新
5. 备注

---

## 1.总述:

### ✨ 特性

#### 🚀 核心功能
- **智能代理采集**：支持网页爬取和本地文件导入
- **多重验证机制**：基础连通性、浏览器可用性、安全性验证
- **透明代理检测**：自动识别会泄露真实IP的代理
- **智能评分系统**：根据代理稳定性动态评分（0-100分）
- **中断恢复**：支持验证过程中断后继续
- **自动维护**：云端GitHub Actions自动更新代理池

#### 🔧 技术特性
- **多协议支持**：HTTP/HTTPS/SOCKS4/SOCKS5
- **异步验证**：高性能异步验证，支持并发
- **SQLite存储**：轻量级数据库，完整代理信息记录
- **Web API**：提供RESTful API接口
- **跨平台**：支持Windows/macOS/Linux

---

### 📁 项目结构

本项目包含两部分,分别为`部署在本地的完全版代码`和`云端公开仓库的actions自动管理代码`

**注意:云端代码已经放入本仓库的cloud_deployment文件夹下**

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
└── <本地 Local> ProxyPool/
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

---

## 🚀 2.快速开始

### 环境要求
- Python 3.8 或更高版本
- 推荐使用虚拟环境

### 安装步骤

#### 从GitHub克隆

**Linux/macOS:**
```bash
# 克隆仓库
git clone https://github.com/limingda1212/ProxyPool.git
cd Proxy-Pool

# 创建虚拟环境（可选）
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

**Windows:**
```
# 使用PowerShell或CMD
git clone https://github.com/limingda1212/ProxyPool.git
cd ProxyPool

# 创建虚拟环境（可选）
python -m venv venv
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 运行
```bash
# 运行主程序
python main.py
# 或
python3 main.py
```

项目自带必要的配置文件和数据库。

---

###  ☁️ 云端部署

为了自动维护代理池，建议部署云端GitHub Actions：

#### 部署步骤

1. **创建新的GitHub仓库**（建议公开,因为不限时长）
   ```bash
   # 在本地创建新目录
   mkdir Proxy-Pool-Actions
   cd Proxy-Pool-Actions
   
   # 复制云端部署文件
   cp -r ../ProxyPool/cloud_deployment/* .
   
   # 初始化Git仓库
   git init
   git add .
   git commit -m "Initial commit: Proxy Pool Actions"
   ```

2. **推送到GitHub**
   ```bash
   # 添加远程仓库（替换为你的仓库URL）
   git remote add origin https://github.com/你的用户名/你的仓库名.git
   git branch -M main
   git push -u origin main
   ```

3. **配置GitHub Token和仓库**
   - 在GitHub上创建Personal Access Token（需要`repo`权限）
   - 在本地程序的设置菜单中添加Token
   - 在本地程序的设置菜单中修改仓库地址

### GitHub Actions 工作流
- **🕐 爬取新代理**：每天北京时间10-12点运行
- **🔄 更新现有代理**：每天北京时间13-15点运行

![Actions状态](https://github.com/LiMingda-101212/Proxy-Pool-Actions/actions/workflows/Crawl-and-verify-new-proxies.yml/badge.svg)
![Actions状态](https://github.com/LiMingda-101212/Proxy-Pool-Actions/actions/workflows/Update-existing-proxies.yml/badge.svg)

---

### 📖 使用指南

#### 主菜单功能

1. **🔍 加载和验证新代理**
   - 从网页爬取或本地文件导入
   - 自动去重和格式检查
   - 支持指定代理类型或自动检测
   - 透明代理检测

2. **🔄 验证代理池代理**
   - 更新现有代理状态
   - 动态调整评分（成功+分，失败-分）
   - 中断恢复功能

3. **🌐 浏览器可用性验证**
   - 使用Playwright测试真实浏览器环境
   - 检测浏览器兼容性问题

4. **🛡️ 代理安全验证(开发中)**
   - DNS劫持检测
   - SSL证书验证
   - 恶意内容检测

5. **📤 提取代理**
   - 按需求提取指定数量代理
   - 支持筛选：类型、地区、分数、安全性
   - 智能负载均衡

6. **📊 查看代理池状态**
   - 实时统计信息
   - 分数分布图表
   - 地区分布分析

7. **☁️ 与云端代理池同步**
   - 合并本地和云端代理池
   - 格式自动转换

8. **🔧 API服务**
   - 启动/停止API服务器
   - 支持多种获取方式
   - 代理状态管理（空闲/忙碌/失效）

9. **⚙️ 设置**
   - 修改配置文件
   - 设置GitHub Token
   - 调整验证参数


**备注:云端和本地同步的功能需要token,请在设置功能(setting)中添加**

---

## 3.代码介绍

### 🎯云端代码 (actions_main.py)

`github actions代理自动管理`

负责与开发者本地代理池对接,由于actions耗时长,所以建议放在一个[公开仓库<点这里查看本项目使用的云端仓库>](https://github.com/LiMingda-101212/Proxy-Pool-Actions)内


#### Workflows工作流

1. 爬取并验证新代理,每天北京时间10-12点运行 - UTC+2
2. 重新验证已有代理,每天北京时间13-15点运行 - UTC+5

#### Actions当前状态

爬取并验证新代理
![Proxy Pool Update](https://github.com/LiMingda-101212/Proxy-Pool-Actions/actions/workflows/Crawl-and-verify-new-proxies.yml/badge.svg)

重新验证已有代理
![Proxy Pool Update](https://github.com/LiMingda-101212/Proxy-Pool-Actions/actions/workflows/Update-existing-proxies.yml/badge.svg)


### 🎯开发者本地主代码 (main.py)

`代理自动管理`

实现较为全面的功能:
- 1 .加载和验证新代理,可从爬虫(自动爬取,根据情况指定类型),本地文件(用于手动添加代理时使用,可以选择代理类型(这样比较快),也可用自动检测(若用自动检测可能较慢))加载,并将通过的代理添加到代理池.新代理使用自动检测类型或指定类型.在验证之前会先将重复代理,错误代理筛除(集合筛选),确保不做无用功.满分100分,新代理只要通过`国内204服务`或`Google的204服务`任一验证就98分,错误代理和无效代理0分.支持透明代理检测功能，识别会泄露真实IP的代理.有中断恢复功能,当验证过程被中断时,会自动保存已完成的代理到代理池,未完成的代理保存到中断文件,下次可选择继续验证可以获取代理信息(城市,运营商等),对于已经有ip信息的代理不重复进行获取信息
- 2 .检验和更新代理池内代理的有效性,使用代理池文件中保存的上次结果类型作为验证使用类型,验证是否支持国内和国外,再次验证成功一个(国内/国外)加1分,全成功加2分,无效代理和错误代理减1分,更直观的分辨代理的稳定性.支持透明代理检测功能，识别会泄露真实IP的代理.
- 3 .浏览器使用验证,部分代理没法在浏览器中使用(安全问题),用`playwright`检测出浏览器可用代理.
- 4 .代理安全验证,检验代理安全性
- 5 .提取指定数量的代理,优先提取分数高,稳定的代理,可指定提取类型,支持范围,是否为透明代理,浏览器是否可用
- 6 .查看代理池状态(总代理数量,各种类型代理的分数分布情况,支持范围,浏览器是否可用统计)
- 7 .与部署在github上由actions自动维护的代理池合并,将github精简格式转为本地全面格式
- 8 .API服务,提供开启和调试功能.为了防止一个代理在不同爬虫被多次使用,使用了代理状态,未调用时`idle`,调用获取会使状态变为`busy`,失败会变为`dead`并很快会被清理.
- 9 .手动清理数据库中的0分代理
- 10 .设置菜单,不用每次手动改`config.json`文件
- 11.帮助菜单,提供帮助信息

### 🎯代理池

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

---

## 📈 4.更新

### (主代码 main.py )

```
<V1.0.0> 2025-12-14 : ✅ 实现了:
    ✳️1.加载和验证新代理,可从爬虫(自动爬取,根据情况指定类型),本地文件(用于手动添加代理时使用,可以选择代理类型(这样比较快),
    也可用自动检测(若用自动检测可能较慢))加载,并将通过的代理添加到代理池文件.新代理使用自动检测类型或指定类型.
    在验证之前会先将重复代理,错误代理筛除(集合筛选),确保不做无用功.
    满分100分,新代理只要通过国外204服务或国内204服务任一验证就98分,错误代理和无效代理0分(会被0分清除函数清除).
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
<V1.1.0> 2025-12-20 : 将程序改为标准代理池,添加了api运行入口,开放多个url用于不同用途的调用.为了防止一个代理在不同爬虫被多次使用,使用了代理状态,未调用时"idle",调用获取会使状态变为"busy",失败会变为"dead"并很快会被清理.
<V1.2.0> 2025-12-21 : 将代理池迁移到SQLite中,围绕数据库进行了改动
<V2.0.0> 2026-01-11 : 将一个main文件分成多个模块,分别实现不同功能
<V2.1.0> 2026-02-12 : 将验证服务改成国际和国内的204服务
<V2.1.1> 2026-02-13 : 项目改名叫ProxyPool(原名Proxy-Pool),版本号改用标准X.Y.Z格式
```

### (云端 actions_main.py)

实现基本的爬取并验证和重新验证已有代理功能

```
<V1.0.0适配> 2025-12-14 : ✅依照主代码编写,爬取验证 与 重新验证 被拆成两个Workflows
    云端代码格式: 类型,代理,分数,是否支持中国,是否支持国际,是否为透明代理,检测到的IP
<V2.1.0适配> 2026-02-12 : 将验证服务改成国际和国内的204服务
```

---

## 5.备注

---

### 📞 支持与反馈

- 📧 问题反馈：GitHub Issues

- 💬 讨论区：GitHub Discussions

- ⭐ 如果喜欢本项目，请给个`Star`！

---

### 🔒 免责声明

关于爬虫功能

**重要声明：**

本项目中的爬虫功能仅用于学习和研究目的。使用者应：

- 遵守法律法规：确保在合法范围内使用爬虫功能
- 尊重网站规则：遵守目标网站的 robots.txt 协议和服务条款
- 控制请求频率：避免对目标网站造成过大压力
- 明确使用目的：不得用于非法或不道德的活动

**开发者声明**

本项目开发者不对以下行为负责：

- 用户违反法律法规使用本项目
- 用户侵犯第三方权益的行为
- 因使用代理造成的任何损失或法律问题

**建议与警告**

🔸 仅使用公开可用的代理源

🔸 不要爬取受版权保护的内容

🔸 避免爬取个人隐私信息

🔸 建议在爬取前获取网站许可

**用户需自行承担使用本项目的所有风险。**

---

### 🙏 致谢

感谢所有开源项目的贡献者，特别是：

- [requests](https://github.com/psf/requests) - HTTP库
- [aiohttp](https://github.com/aio-libs/aiohttp) - 异步HTTP库
- [playwright-python](https://github.com/microsoft/playwright-python) - 浏览器自动化

---

### 📄 开源协议

本项目采用 GNU General Public License v3.0 (GPL v3) 开源协议。

主要条款：

- 自由使用：可以自由使用、复制、分发本项目
- 开源要求：修改本项目后，必须以相同协议开源
- 免责声明：不提供任何担保
- 完整协议内容请查看 [LICENSE](LICENSE) 文件。

---
