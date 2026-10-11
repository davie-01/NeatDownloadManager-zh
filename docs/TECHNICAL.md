# 实现说明

## NIB 汉化

NIB 使用 NSKeyedArchiver 的 `$objects` / UID 引用。上游通过字符串替换汉化，但某些文本也被图片名、动作或内部标识共用；例如 Resume 同时是按钮显示文字与图标资源名。直接替换字符串会影响资源查找。

本实现保留全部原对象，追加中文字符串，仅改变已识别的显示属性引用：NSContents、NSDev、NSWindowTitle、NSTitle、NSSegmentItemLabel、工具栏显示名称/提示，以及 NSTabViewItem 的 NSLabel。动作、出口、类名、资源名及其他属性保持原值。每个 NIB 构建后重新解析并验证差异，详细修改列在构建报告中。翻译查询会规范化 HTML 实体及空白。

## 工具栏与菜单命令

1.3.24 的 `toolBtnAction:` 依据英文按钮标题进行命令分发。只改 NIB 会让设置、关于等按钮失效，因此同步调整两个架构的 13 个命令 CFString 对象，总共 26 处。

中文 UTF-16 数据存放在每个架构 `__TEXT` 头部已验证为空的区域，从相对位置 `0x1800` 开始；更新对应 CFString 的标志、指针和长度。原始 `__cstring` 段逐字节保持不变。存储必须位于原 `__text` 之前，并与 `0x1100` 开始、最大 `0x700` 字节的侧边栏代码分离。构建不增加段大小，不移动代码。

1.0.0 曾在原 ASCII 槽位存放 UTF-16，并全局翻译分类对象。但相同存储也被 C++ 代码直接引用。视频分类在转换及写入下载记录时产生 nil，随后 `appendString:` 抛出异常，使下载弹窗停留在异常状态；浏览器送入的下载也会经过此路径。1.0.1 保留原 ASCII 和内部分类对象，真实原版二进制回归检查覆盖这两项。

## 侧边栏名称

Complete、Incomplete、All Downloads、Video、Audio、Compressed、Document、Misc 同时影响内部分类、状态或图标，不能全局翻译。本补丁保持这 8 个原始常量不变，仅包装侧边栏最终 `setStringValue:` 调用。

两种架构在 `__TEXT` 头部空闲空间 `0x100001100` 放置包装代码，通过 `isEqualToString:` 识别 8 个名称，在最终显示时转成中文；其他字符串及 nil 原样传递，再调用原 objc_msgSend。调用位置和 Objective-C 引用位置仅适配经过指纹确认的 1.3.24。

## Command-W

`NDMWindowShortcuts.m` 编译为 universal 动态库，通过增加 LC_LOAD_DYLIB 加载：`@executable_path/../Frameworks/NDMWindowShortcuts.dylib`。加载命令必须位于侧边栏包装代码之前且原空间为空。

模块在主线程注册本进程的 NSEvent 局部键盘事件处理，识别 Command-W，拒绝额外 Shift / Option / Control 修饰键。Caps Lock 等无关标志不影响识别；重复按键事件被吞掉，避免连续关闭窗口。

普通可关闭窗口调用 `performClose:`，沿用窗口自身的代理和关闭行为。附属 sheet 优先调用可见且启用的取消/关闭按钮；没有对应按钮时调用 `endSheet: returnCode:NSModalResponseCancel` 并隐藏 sheet，不关闭父窗口。

## 构建与安装边界

先校验原版版本、可执行文件 SHA-256、全部 NIB 文件集合和哈希。修改复制到临时目录的应用，不修改输入。输入原版整包也须通过严格签名验证。编译完成后仅对新增动态库及主应用进行本地签名，最后用 `codesign --verify --deep --strict` 验证整包。**签名时不用 `--deep`**，避免递归重签官方 Safari 扩展并剥离其沙盒权限。签名前后校验 `Contents/PlugIns` 全部文件 SHA-256，要求与官方输入逐文件一致，再输出构建结果。

安装先确认进程已完全退出，复制完整应用并核对文件哈希与签名，再通过同文件系统目录重命名替换。旧应用先复制至项目根目录 `backup/`，逐文件校验后写入 JSON 恢复记录；项目位于不同磁盘时也可备份。目标目录中的隐藏临时目录仅在替换过程中保留原应用以便回滚，正常完成后自动清理。失败应用副本也保存在项目 `backup/`。测试覆盖替换后的校验失败时恢复原应用，避免在错误处理中删除正在使用的应用。备份记录包含本机路径，应保留在忽略目录中。

原 NIB 和可执行文件由使用者自行提供，源码仓库只保存翻译、补丁代码和兼容指纹。

## 一键安装入口

`install.sh` 按自身所在位置解析项目根目录，调用 `quick_install.py`。原版输入固定为 `original/NeatDownloadManager.app`；首先检查其存在及兼容性。默认安装前检查目标、运行状态及目录权限，构建完成后复用原整包安装器并再次检查运行状态。`--build-only` 不要求退出当前应用。每次构建位于独立的 `build/install-时间戳/`。
