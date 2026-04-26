# 日程安排 iOS 安装、测试与上架操作手册

## 1. 这份文档解决什么问题

这份文档是给你在**借到朋友 Mac 电脑之后**直接照着操作用的，目标是完成下面几件事：

1. 把手机端项目在 Mac 上跑起来
2. 用 Xcode 安装到你自己的 iPhone
3. 后续继续维护时，知道代码应该怎么从 Windows 同步到 Mac
4. 上传到 TestFlight 给朋友测试
5. 最后正式上架到 App Store

---

## 2. 先明确你的项目路线

你这个项目当前更合理的手机端路线，不是把 Windows 桌面端原样搬到 iPhone，而是：

- 桌面端继续保留：Windows + 本地 FastAPI + 本地 SQLite
- 手机端单独做：Vue 手机端 / Capacitor iOS App
- 云端负责：账号、设备、云同步
- AI Key 继续保存在用户设备本地，不走你的云服务器

所以 iPhone 端应理解为：

- 一个单独的移动端客户端
- 通过云同步服务和桌面端互通
- 不在 iPhone 上直接跑你现在这套本地 Python FastAPI

---

## 3. 借到朋友 Mac 后，你应该先下载什么

建议你在 Mac 上先准备下面这些：

### 3.1 必装

1. **Xcode**
   - 用来打开 iOS 工程
   - 用来签名、真机安装、Archive、上传 TestFlight / App Store

2. **你的 Apple ID**
   - 建议用你自己的 Apple ID 登录 Xcode
   - 不要用朋友的 Apple ID 给你的 App 做签名和上架
   - 如果只是先真机安装测试，也建议从一开始就用你自己的 Apple 账号

3. **Node.js（建议 LTS 版本）**
   - 你的手机端还是前端项目，需要在 Mac 上执行 `npm install`、`npm run build`

4. **项目代码**
   - 最好用 Git 拉取
   - 不建议长期靠微信传压缩包、U 盘来回拷

### 3.2 建议安装

1. **Git**
   - 用来 `clone / pull / push`
   - 方便你以后 Windows 开发、Mac 打包的协作流程

2. **VS Code**
   - 如果你需要在 Mac 上临时改一些小问题，会方便很多
   - 但主开发机仍建议保留在你自己的 Windows 电脑上

---

## 4. 你后续维护，应该怎么更新代码

## 4.1 推荐工作流：Windows 主开发，Mac 负责 iOS 构建和分发

这是最适合你当前情况的方式。

### 你平时开发时
在你自己的 Windows 电脑上：

- 用 VS Code / Codex 开发
- 跑前端和后端
- 测功能
- 提交代码到 Git 仓库

### 你要装到 iPhone、发 TestFlight、准备上架时
在借来的 Mac 上：

- 拉最新代码
- 构建手机端
- 同步 iOS 工程
- 用 Xcode 真机运行 / Archive / 上传

## 4.2 最推荐的同步方式：Git

### Windows 上
每次开发完成：

```bash
git add .
git commit -m "update: mobile app"
git push
```

### Mac 上
每次拿到最新代码：

```bash
git pull
```

如果 Mac 上是第一次拿项目：

```bash
git clone <你的仓库地址>
```

## 4.3 不推荐的方式

不建议长期这样维护：

- Windows 改完打包成 zip 发到 Mac
- Mac 上改完又拷回 Windows
- 两边代码版本混乱

因为后面你一旦开始真机调试、修 iOS 特有问题、改签名配置，很容易乱。

---

## 5. 在 Mac 上第一次准备项目

下面假设你的手机端项目目录叫：

```text
schedule_mobile/
```

如果你现在还没单独拆出手机端项目，也建议尽快单独建一个移动端目录，不要直接把桌面端前端拿来硬上 iPhone。

### 5.1 进入项目目录

```bash
cd 你的项目目录/schedule_mobile
```

### 5.2 安装依赖

```bash
npm install
```

### 5.3 构建前端资源

```bash
npm run build
```

### 5.4 同步到 iOS 工程

```bash
npx cap sync ios
```

### 5.5 打开 Xcode

```bash
npx cap open ios
```

---

## 6. 怎么用 Xcode 安装到你自己的 iPhone

这是你最先要跑通的关键步骤。

## 6.1 准备工作

1. 用数据线把 iPhone 连到 Mac
2. 手机上如果弹出“信任此电脑”，点信任
3. Mac 上打开 Xcode
4. 在 Xcode 里登录你自己的 Apple ID

## 6.2 在 Xcode 里做签名配置

打开 iOS 工程后，做这些设置：

1. 选中项目
2. 选中 App Target
3. 打开 **Signing & Capabilities**
4. 勾选 **Automatically manage signing**
5. Team 选择你自己的账号或开发者团队
6. 确保 **Bundle Identifier** 唯一  
   例如：

```text
com.yourname.schedule
```

不要和别人的包名冲突。

## 6.3 选择运行目标

在 Xcode 顶部设备列表里：

- 选择你的 iPhone 真机
- 不要选模拟器（如果你要真正装到手机）

## 6.4 运行安装

点击 Xcode 顶部的 **Run** 按钮。

成功后：

- App 会被安装到你的 iPhone 上
- 第一次可能需要在手机里信任开发者签名
- 如果有提示，就去手机设置里按提示完成信任

## 6.5 如果你只是自己真机测试

这一阶段的目标不是马上上架，而是先确认：

- App 能打开
- 登录能用
- 云同步能用
- AI 配置页能用
- 基本页面能正常显示
- 不会一打开就崩

---

## 7. 你应该怎么做“维护 + 真机安装”的日常流程

以后你每次更新版本，建议都固定成这个顺序。

## 7.1 Windows 上开发

```bash
git add .
git commit -m "update: mobile feature"
git push
```

## 7.2 Mac 上更新

```bash
git pull
npm install
npm run build
npx cap sync ios
npx cap open ios
```

然后回到 Xcode：

- 点 Run，重新安装到你的手机
- 验证新改动

## 7.3 什么时候需要重新 `npx cap sync ios`

一般来说，只要你有下面这些情况，就要重新 sync：

- 前端代码更新
- Capacitor 插件变化
- 配置变化
- 图标 / 启动图 / 权限声明变化

如果只是 Xcode 里的纯原生签名设置改动，不一定每次都要 sync。

---

## 8. 怎么上传到 TestFlight

当你手机上跑通后，下一步最实用的是 TestFlight，而不是立刻正式上架。

因为 TestFlight 很适合：

- 你自己多设备测试
- 给朋友、同学、对象先试用
- 先发现问题，再决定是否上架

## 8.1 你需要什么条件

要用 TestFlight，建议你准备好：

1. **Apple Developer Program**
2. **App Store Connect**
3. Xcode 中可正常 Archive 的工程
4. 唯一 Bundle ID
5. 基本 App 信息

## 8.2 在 App Store Connect 先创建应用记录

你需要先在 App Store Connect 里创建这个 App：

- App 名称
- 平台 iOS
- Bundle ID
- SKU（你自己定义一个唯一标识）

建议：

- App 名称尽量和最终上架名一致
- Bundle ID 不要后面频繁改
- SKU 自己记得住即可

## 8.3 用 Xcode 上传构建

在 Xcode 里：

1. 选择 **Any iOS Device (arm64)** 或等价归档目标
2. 菜单里选择 **Product → Archive**
3. 等归档完成后进入 Organizer
4. 选择最新 Archive
5. 点击 **Distribute App**
6. 选择 **App Store Connect**
7. 继续上传

上传成功后，去 App Store Connect 等待 build 处理完成。

## 8.4 在 TestFlight 里分发测试

处理完成后，你可以在 TestFlight 页面看到这个 build。

你可以分两种方式测试：

### 方式 A：内部测试
适合你自己或少量共同管理 App 的成员。

### 方式 B：外部测试
适合邀请朋友、同学、小范围真实用户。

外部测试通常更适合你说的“让朋友几个人也下载测试”。

---

## 9. 怎么让朋友几个人下载测试使用

你有两个主要方法：

## 9.1 方法一：TestFlight 外部测试（最推荐）

这是最适合“朋友几个人先下载测试”的方式。

流程是：

1. 你把 build 上传到 App Store Connect
2. 在 TestFlight 创建外部测试组
3. 添加要测试的 build
4. 填好测试信息
5. 等第一版外部测试 build 通过 TestFlight 审核
6. 邀请朋友加入测试

朋友收到邀请后：

- 在 iPhone 上安装 **TestFlight**
- 点你的邀请链接或邮件邀请
- 安装测试版 App

### 这种方式的优点
- 最接近正式上架前的真实体验
- 方便反复更新测试版本
- 朋友不用插线，不用 Xcode，不用 Mac
- 你后面继续更新版本也很方便

## 9.2 方法二：注册设备后单独分发
这个更麻烦，不适合你当前阶段。

因为你还要：

- 收集朋友手机的设备信息
- 注册设备
- 做更复杂的签名分发

所以对你现在来说，不推荐优先走这条。

---

## 10. 正式上架 App Store 怎么做

等 TestFlight 跑顺了，再走正式上架。

## 10.1 上架前你必须准备的东西

至少准备这些：

1. App 名称
2. 唯一 Bundle ID
3. App 图标
4. 各尺寸截图
5. App 描述、副标题、关键词
6. 隐私政策 URL
7. App Privacy 填写
8. 审核说明
9. 测试账号（如果审核需要登录）
10. 版本号和构建号

## 10.2 你的项目有一个特别重要的审核点

因为你的产品路线里已经明确会做：

- 账号系统
- 云同步
- 用户数据

所以如果 App 支持用户创建账号，那么你在 App 内最好同时提供：

- 删除账号入口
- 或至少发起账号删除的入口

这是后面正式提审时很重要的一点，建议你在正式上架前补齐。

## 10.3 上架步骤

### 第一步：在 App Store Connect 完善信息
填写：

- App 名称
- 分类
- 描述
- 截图
- 隐私政策
- 联系方式
- App Privacy

### 第二步：上传正式候选版本
还是在 Xcode 中：

- Product → Archive
- Organizer → Distribute App
- 上传到 App Store Connect

### 第三步：在 App Store Connect 选中该 build
把刚上传的 build 关联到当前版本。

### 第四步：填写审核信息
例如：

- 审核账号
- 审核密码
- 特殊测试说明
- 云同步如何测试
- AI 功能是否需要单独配置
- 如果某些功能默认关闭，要告诉审核员怎么进入

### 第五步：提交审核
提交后等待 Apple 审核。

---

## 11. 你这个项目在上架前建议重点检查什么

这是结合你现在项目情况给你的专门清单。

## 11.1 功能层面
- 登录是否稳定
- 云同步是否稳定
- 离线后恢复是否正常
- 学习记录是否正常显示
- 今日任务和长期任务是否正常
- AI 配置页是否不会误导用户
- 没填 AI Key 时，错误提示是否清晰

## 11.2 合规层面
- 有隐私政策
- 有用户支持联系方式
- 如果支持账号创建，要有删除账号入口
- 不要把 AI Key 上传到你的云服务器
- 不要把隐私数据写进公开日志

## 11.3 提审体验
- 提供可测试账号
- 提供测试步骤
- 解释哪些功能依赖云同步
- 解释 AI 功能需要用户自己配置 Key，默认是否可跳过

---

## 12. 你最适合的实际推进顺序

你现在最稳的推进顺序应该是：

### 第 1 步
先把手机端项目在 Mac 上跑起来。

### 第 2 步
先装到你自己的 iPhone 上测试。

### 第 3 步
修掉明显 bug，确保最基础流程能用：
- 打开 App
- 登录
- 同步
- 任务查看/完成
- 设置页可用

### 第 4 步
上传 TestFlight。

### 第 5 步
邀请 3 到 5 个朋友测试。

### 第 6 步
根据 TestFlight 反馈修 bug。

### 第 7 步
准备正式 App Store 上架资料，再提交审核。

---

## 13. 朋友几个人测试时，你应该怎么安排

建议不要一下子发给很多人。

### 第一轮测试
先给最熟的人：
- 你自己
- 1 个 iPhone 朋友
- 1 个你信得过、愿意反馈问题的人

目标：
- 看会不会闪退
- 看登录和同步是否稳定
- 看手机端 UI 是否适配正常

### 第二轮测试
扩大到 3 到 10 个人。

重点看：
- 是否有人登录失败
- 是否有人同步失败
- 是否 AI 配置页看不懂
- 是否有人不知道怎么开始用

---

## 14. 你拿到朋友 Mac 后最推荐的实际操作清单

你可以直接照这个顺序做。

### 第一天先做这些
1. 安装 Xcode
2. 登录你自己的 Apple ID
3. 安装 Node.js
4. 拉项目代码
5. `npm install`
6. `npm run build`
7. `npx cap sync ios`
8. `npx cap open ios`
9. 用 Xcode 安装到你自己的 iPhone

### 第二天做这些
1. 修真机问题
2. 再次安装到手机
3. 准备 App Store Connect
4. 创建 App 记录
5. 用 Xcode Archive 并上传 build
6. 开 TestFlight

### 后续做这些
1. 邀请朋友测试
2. 修反馈
3. 准备截图、描述、隐私政策
4. 最后提交 App Store 审核

---

## 15. 你以后长期维护的最优解

一句话：

**Windows 继续做主开发机，Mac 只负责 iOS 构建、真机安装、TestFlight 和上架。**

也就是说：

- 平时开发：Windows + VS Code
- 代码同步：Git
- iOS 安装/测试/上架：Mac + Xcode

这样最省事，也最符合你现在项目现状。

---

## 16. 你的最终操作模板

### 日常开发更新模板

#### Windows
```bash
git add .
git commit -m "update: mobile app"
git push
```

#### Mac
```bash
git pull
npm install
npm run build
npx cap sync ios
npx cap open ios
```

然后在 Xcode：
- Run 安装到手机
- 或 Archive 上传 TestFlight / App Store

---

## 17. 一句话总结

你现在最应该做的不是一下子研究完整上架细节，而是：

**先拿到 Mac，把项目装到你自己的 iPhone 上跑起来；再走 TestFlight 给朋友测试；最后再准备正式上架资料。**
