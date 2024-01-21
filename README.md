# auto_miyoushe_signin

基于文字识别的米游社自动签到脚本。

所有功能通过文字识别实现，无需 cookie，很少出现验证码，目前真正实用的签到工具。

## 功能
- 自动领取米游社签到福利
  - 包括原神、崩坏：星穹铁道、崩坏 3 等
  - 也支持米游社社区自动打卡
- 支持企业微信、钉钉等多个推送渠道
  - 详情请前往 [onepush](https://github.com/y1ndan/onepush) 页面查看

## 环境要求(windows x64)

- python >=3.6
- 一个支持 adb 的模拟器

## 安装依赖

```sh
pip install -r requirements.txt
```

## 用法

1. 复制根目录下的 `config.example.yml` 文件，并改为 `config.yml`
2. 填写 `ADB_PORT` (必须)、`CLOCK_IN_BBS`(可选)、`ONEPUSH_CONFIG`(可选)。`ADB_PORT` 为要连接的模拟器的 adb 端口，可查询各大模拟器文档获取；`CLOCK_IN_BBS`为是否在对应游戏的米游社打卡，默认为 `true`；`ONEPUSH_CONFIG` 为  [onepush](https://github.com/y1ndan/onepush) 相关配置，请自行了解
3. 启动已安装好米游社的模拟器
4. 确认 adb 可用。若不可用，请添加 adb 到环境变量

   ```sh
   adb devices
   ```
5. 运行 `python auto_miyoushe_signin.py`
6. 查看运行结果

## 可能出现的问题

### 如何每日运行

- 可在`我的电脑`中添加系统任务来每日运行

- 修改脚本实现死循环运行
- 其他方式每日触发脚本运行

### 有部分游戏未签到/签到失败

- 由于综合（大别野）是没有签到福利的，所以固定签到失败。（打卡功能是正常的）
- 对于未绑定角色的游戏，固定签到失败。
- 由于 tab 栏的限制，所以识别的时候只能识别到当前页面显示的所有 tab
  - 目前是按照 原神、综合、星穹铁道、绝区零、崩坏 3、未定事件簿、崩坏学园 2 的顺序来签到的
- 可以修改米游社的 tab 排序，和项目中的一致即可
- 也可以修改脚本中的 tab 排序
- 为减少 tab 问题，可减少 tab 的数量，使之可以在一个屏幕内展示出来

## 作者


👤 **CaoMeiYouRen**

* Website: [https://blog.cmyr.ltd/](https://blog.cmyr.ltd/)
* GitHub: [@CaoMeiYouRen](https://github.com/CaoMeiYouRen)

## 📝 License

Copyright © 2024 [CaoMeiYouRen](https://github.com/CaoMeiYouRen).<br />
This project is [AGPL-3.0](https://github.com/CaoMeiYouRen/auto_miyoushe_signin/blob/master/LICENSE) licensed.
