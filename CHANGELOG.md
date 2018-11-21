## 1.5 (2018/11/21)
### Enhancements
- 增加库查找时，支持已发布的 ArtifactId
### Bug Fixes
- 单项目某些情况下，导致 sorted_modules 为空，deploy all 无效
### Changes
- 不在强制在 grade.properties 中配置发布仓库的信息配置
- 如使用 include deploy 模式，可能会出现 sync failed，建议改用新版方式，命令行多指定目录（AS 3.4 Cancry 版本修复）

## 1.4 (2018/10/23)
### Bug Fixes
- 1.3 版本变量名调整遗漏导致变量名处于命名遮罩且不工作
### Changes
- 加强版本升级支持模板
  *  `0.1-alpha1` -> `0.1-alpha2`
  *  `1` -> `2`
  *  `0.1` -> `0.2`
  *  `0.1-alpha1-test` -> `0.1-alpha2-test`
  *  `0.1-alpha1-test1` -> `0.1-alpha1-test2`
  
## 1.2 （2018/9/19）
### Enhancements
- 支持在 pom.properties 中配置哪些要发布，如 api compile
### Changes
- 绕过一些可能为空的依赖发布项信息
  
## 1.1 (2018/07/31)
### Enhancements
- 增加 -l 对输出 mavenLocal 的支持
- 增加配置 module 的发布类型
  - 可单独配置 module 的 MavenType、ArtifactId、GroupId
  - eg. LibAMavenType = release
- 遍历 Module 依赖时，过滤 lint-gradle 依赖
- 增加 -i >>> --info --stacktrace

### Bug Fixes
- 修复更新 module 信息时出现正则误匹配
  - eg. AModule 、AAModule，当修改 AModule 时，AAModule 误修改

### Changes
- 配置 -u 时改为强制升级，无论当前是 snapshot 还是 release
- 配置 -r 时改为强制设置 release，并重写 version_properties.gradle 中的配置，优先于 -u
- deploy mode 默认为 -a
  - python deploy.py [-a]
- 移除 artifactory.gradle 中 android 的判断

## 1.0 
  fork from https://github.com/luckybilly/OKDALM 
