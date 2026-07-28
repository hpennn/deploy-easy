# 智能部署助手 - App 打包与上架指南

本文档面向零基础用户，详细说明如何将「智能部署助手」前端项目打包为原生 Android APK 和 iOS App，并上架到各大应用市场。

---

## 目录

- [一、前置要求](#一前置要求)
- [二、运行模式说明](#二运行模式说明)
- [三、Android APK 打包步骤](#三android-apk-打包步骤)
- [四、iOS App 打包步骤](#四ios-app-打包步骤)
- [五、应用市场上架指南](#五应用市场上架指南)
- [六、审核注意事项](#六审核注意事项)
- [七、费用参考表](#七费用参考表)

---

## 一、前置要求

### 1.1 基础环境

| 工具 | 版本要求 | 说明 |
|------|----------|------|
| Node.js | ≥ 18.x | 运行 Capacitor CLI |
| npm | ≥ 9.x | 包管理器（随 Node.js 安装） |
| Git | ≥ 2.x | 版本控制 |

### 1.2 Android 打包需要

| 工具 | 说明 |
|------|------|
| Android Studio | 最新版，含 Android SDK |
| Java JDK | 17+（Android Studio 自带） |
| Gradle | 7.x+（Android Studio 自带） |

**安装步骤：**
1. 前往 https://developer.android.com/studio 下载 Android Studio
2. 安装时勾选 Android SDK、Android SDK Platform
3. 打开 Android Studio → Tools → SDK Manager，安装 API Level 33+

### 1.3 iOS 打包需要

| 工具 | 说明 |
|------|------|
| Mac 电脑 | macOS 13+ |
| Xcode | 15+（App Store 免费下载） |
| Apple Developer 账号 | $99/年（上架必需） |

---

## 二、运行模式说明

Capacitor 支持两种运行模式，可根据需求灵活切换：

### 2.1 线上模式（当前配置）

```typescript
server: {
  url: 'https://deploy.zhinenti.cn',  // 加载线上页面
}
```

**特点：**
- App 启动后直接加载线上网页
- 更新前端无需重新打包上架，改完代码刷新即生效
- App 体积更小（不包含前端静态文件）
- 需要用户联网才能使用

**适用场景：** 频繁更新前端、希望用户始终使用最新版本

### 2.2 离线模式（打包静态文件）

```typescript
// 注释掉 server.url，App 将加载本地打包的静态文件
// server: {
//   url: 'https://deploy.zhinenti.cn',
// },
```

**特点：**
- 前端文件打包在 App 内部，无需网络即可打开
- 更新前端需要重新打包 + 重新上架
- App 体积更大（包含所有前端文件）
- 可离线使用

**切换步骤：**
1. 编辑 `capacitor.config.ts`，注释掉 `server.url`
2. 确保 `frontend/` 目录包含完整的前端文件
3. 执行 `npx cap sync` 同步

> 💡 **建议**：初期推荐使用线上模式，方便快速迭代。稳定后可考虑离线模式。

---

## 三、Android APK 打包步骤

### 3.1 初始化项目

```bash
# 1. 进入项目目录
cd deploy-easy

# 2. 安装依赖
npm install

# 3. 同步 Web 资源到原生平台
npx cap sync
```

### 3.2 添加 Android 平台（首次）

```bash
# 添加 Android 平台
npx cap add android

# 同步最新代码
npx cap sync
```

### 3.3 生成 APK

**方式一：通过 Android Studio（推荐）**

```bash
# 用 Android Studio 打开项目
npx cap open android
```

在 Android Studio 中操作：
1. 等待 Gradle 同步完成（首次可能需要下载依赖，耐心等待）
2. 点击菜单栏 **Build → Generate Signed Bundle / APK**
3. 选择 **APK** → Next
4. 创建或选择密钥库（keystore）
   - 首次需要创建：点击 **Create new**
   - 填写密码、有效期等信息
   - ⚠️ **务必妥善保存密钥库文件和密码**，后续更新必须用同一个
5. 选择 **release** → Next
6. 选择输出位置 → **Finish**
7. 生成完成后，APK 位于 `android/app/release/` 目录

**方式二：命令行打包**

```bash
cd android

# 生成 release APK
./gradlew assembleRelease

# APK 输出位置
# android/app/build/outputs/apk/release/app-release-unsigned.apk
```

### 3.4 签名配置

正式上架的 APK 必须签名。在 `android/app/build.gradle` 中配置：

```groovy
android {
    signingConfigs {
        release {
            storeFile file('your-keystore.jks')
            storePassword 'your-store-password'
            keyAlias 'your-key-alias'
            keyPassword 'your-key-password'
        }
    }
    buildTypes {
        release {
            signingConfig signingConfigs.release
        }
    }
}
```

### 3.5 测试 APK

```bash
# 用 Android Studio 打开后，连接手机或模拟器
# 点击运行按钮 ▶️ 即可安装到设备
```

---

## 四、iOS App 打包步骤

### 4.1 前提条件

- 必须使用 Mac 电脑
- 已安装 Xcode（App Store 免费下载）
- 已注册 Apple Developer 账号（$99/年）

### 4.2 添加 iOS 平台

```bash
# 添加 iOS 平台
npx cap add ios

# 同步代码
npx cap sync
```

### 4.3 在 Xcode 中配置

```bash
# 用 Xcode 打开项目
npx cap open ios
```

在 Xcode 中操作：
1. 选择项目根节点 → **Signing & Capabilities**
2. 勾选 **Automatically manage signing**
3. 选择你的 Apple Developer Team
4. 确认 Bundle Identifier 为 `com.zhinenti.deploy`

### 4.4 Archive 打包

1. 在 Xcode 顶部选择设备为 **Any iOS Device (arm64)**
2. 菜单栏 **Product → Archive**
3. 等待 Archive 完成（可能需要几分钟）
4. 完成后自动打开 Organizer 窗口
5. 选择本次 Archive → **Distribute App**
6. 选择 **App Store Connect** → **Upload**
7. 按提示完成上传

---

## 五、应用市场上架指南

### 5.1 华为应用市场（AppGallery）

**注册流程：**
1. 访问 https://developer.huawei.com/consumer/cn/
2. 点击「注册」→ 选择「企业开发者」或「个人开发者」
3. 填写信息、完成实名认证（免费）
4. 审核通过后即可创建应用

**上架步骤：**
1. 登录华为开发者联盟 → 「应用市场」→「我的应用」
2. 点击「创建应用」→ 选择「手机和平板」
3. 填写应用信息：
   - 应用名称、简介、详细描述
   - 应用图标（512×512 PNG）
   - 应用截图（至少 3 张，16:9 或 9:16）
   - 隐私政策链接
4. 上传 APK 文件
5. 选择分类、设置年龄分级
6. 填写软件著作权信息（部分情况需要）
7. 提交审核（通常 1-3 个工作日）

### 5.2 小米应用商店

**注册流程：**
1. 访问 https://dev.mi.com/distribute/doc/details?pId=1126
2. 注册小米开发者账号
3. 完成实名认证（个人/企业均可，免费）

**上架步骤：**
1. 登录小米开放平台 → 「应用管理」→「创建应用」
2. 填写应用信息（名称、描述、图标、截图）
3. 上传 APK
4. 填写隐私政策链接
5. 提交审核（通常 1-3 个工作日）

### 5.3 OPPO 应用商店

**注册流程：**
1. 访问 https://open.oppomobile.com/
2. 注册 OPPO 开放平台账号
3. 完成开发者认证（免费）

**上架步骤：**
1. 登录 → 「应用发布」→「新应用发布」
2. 填写应用信息
3. 上传 APK
4. 提交审核（通常 1-3 个工作日）

### 5.4 vivo 应用商店

**注册流程：**
1. 访问 https://dev.vivo.com.cn/
2. 注册 vivo 开放平台账号
3. 完成开发者认证（免费）

**上架步骤：**
1. 登录 → 「应用管理」→「上传应用」
2. 填写应用信息
3. 上传 APK
4. 提交审核（通常 1-3 个工作日）

### 5.5 Google Play

**注册流程：**
1. 访问 https://play.google.com/console/
2. 使用 Google 账号登录
3. 支付一次性注册费 **$25**（约 180 元人民币）
4. 完成开发者信息验证

**上架步骤：**
1. 在 Google Play Console 点击「创建应用」
2. 填写应用详情：
   - 应用名称、描述（需英文 + 各语言版本）
   - 应用图标（512×512）
   - 特色图片（1024×500）
   - 截图（至少 2 张）
3. 设置内容分级（需填写问卷）
4. 设置定价和分发国家
5. 填写隐私政策链接
6. 上传 AAB 文件（注意：Google Play 要求 AAB 格式而非 APK）
7. 提交审核（首次审核可能需要 3-7 天）

**生成 AAB 文件：**
```bash
cd android
./gradlew bundleRelease
# 输出位置: android/app/build/outputs/bundle/release/app-release.aab
```

### 5.6 Apple App Store

**前提条件：**
- Apple Developer 账号（$99/年，约 688 元人民币）
- Mac 电脑 + Xcode

**上架步骤：**
1. 登录 https://appstoreconnect.apple.com/
2. 点击「我的 App」→「+」→「新建 App」
3. 填写 App 信息：
   - 名称、副标题、隐私政策 URL
   - 分类选择
4. 准备 App 资产：
   - 图标（1024×1024）
   - 截图（6.7" 和 5.5" 各需一套）
   - 描述文本
5. 通过 Xcode Archive 上传构建版本（见第四章）
6. 在 App Store Connect 中选择上传的构建版本
7. 填写审核信息（测试账号等）
8. 提交审核（通常 1-3 天，首次可能更长）

---

## 六、审核注意事项

### 6.1 通用注意事项

| 项目 | 要求 |
|------|------|
| **隐私政策** | 必须提供有效的隐私政策页面链接 |
| **应用图标** | 清晰、无版权争议、不含「测试」字样 |
| **应用截图** | 真实反映应用功能，不可过度美化 |
| **应用描述** | 如实描述功能，不得夸大宣传 |
| **权限申请** | 只申请必要权限，不申请与功能无关的权限 |
| **内容合规** | 不含违法违规内容 |

### 6.2 国内市场特别注意

- **ICP 备案**：部分应用市场要求应用有 ICP 备案号
- **软件著作权**：部分市场（如华为）可能要求提供软件著作权证书
- **实名认证**：开发者账号需完成实名认证
- **隐私合规**：需符合《个人信息保护法》要求，首次启动需展示隐私协议弹窗

### 6.3 Google Play 特别注意

- **数据安全声明**：需声明收集的用户数据类型
- **内容分级**：必须完成 IARC 内容分级问卷
- **64 位要求**：必须支持 64 位架构
- **Target API Level**：必须 target 最新 API Level（目前为 34）
- **AAB 格式**：必须上传 AAB 而非 APK

### 6.4 App Store 特别注意

- **审核指南**：严格遵守 Apple 审核指南（App Store Review Guidelines）
- **测试账号**：如需登录，必须提供测试账号
- **App 追踪**：需声明 App Tracking Transparency 使用情况
- **元数据**：描述中不得包含价格、其他平台信息等
- **内购**：如有付费功能，必须使用 Apple 内购系统（IAP）

---

## 七、费用参考表

| 项目 | 费用 | 备注 |
|------|------|------|
| **华为开发者** | 免费 | 实名认证免费 |
| **小米开发者** | 免费 | 实名认证免费 |
| **OPPO 开发者** | 免费 | 实名认证免费 |
| **vivo 开发者** | 免费 | 实名认证免费 |
| **Google Play** | $25（一次性） | 约 180 元人民币 |
| **Apple Developer** | $99/年 | 约 688 元人民币/年 |
| **软件著作权** | ¥0~300 | 自行申请免费，代办约 200-300 元 |
| **域名（已有）** | - | deploy.zhinenti.cn |
| **服务器（已有）** | - | 当前部署服务器 |

### 费用汇总

- **仅上架国内市场**：**¥0**（全免费）
- **上架 Google Play**：**约 ¥180**（一次性）
- **上架 App Store**：**约 ¥688/年**
- **全平台上架总计**：**约 ¥868/年**（首年）

---

## 八、常用命令速查

```bash
# 安装依赖
npm install

# 同步 Web 资源到原生平台
npm run cap:sync

# 打开 Android Studio
npm run cap:android

# 打开 Xcode
npm run cap:ios

# 切换到离线模式
# 1. 编辑 capacitor.config.ts，注释掉 server.url
# 2. 运行 npx cap sync
```

---

## 九、常见问题

### Q1: 打包后 App 打开是白屏？
- 检查网络连接（线上模式需要网络）
- 检查 `capacitor.config.ts` 中的 `server.url` 是否正确
- 检查 HTTPS 证书是否有效

### Q2: Android 打包签名忘了怎么办？
- 签名丢失无法恢复，必须用新的签名重新打包
- Google Play 可以使用 Play App Signing 避免此问题
- 国内市场需要卸载旧版后重新安装

### Q3: 上架被拒怎么办？
- 仔细阅读拒绝原因
- 修改对应问题后重新提交
- 大部分市场支持申诉或联系审核人员

### Q4: 如何更新 App？
- **线上模式**：直接更新网站代码，App 自动加载最新内容
- **离线模式**：修改代码 → `npx cap sync` → 重新打包 → 重新上架

---

> 📝 本文档基于 Capacitor 6.x 编写，最后更新：2025 年
