# SIP over WebSocket (Testing Client)

## راه‌اندازی WebSocket در Kamailio

### تماس‌ از طریق WebSocket

کلاینت SIP می‌تواند تماس‌های SIP را از طریق WebSocket برقرار و دریافت کند که ارتباطات را از طریق این پروتکل‌ وب امکان‌پذیر می‌کند.

### تنظیمات فایل kamailio.cfg

برای فعال کردن پشتیبانی از WebSocket در Kamailio، لازم است فایل پیکربندی Kamailio را بر اساس [مستندات ماژول WebSocket در Kamailio](https://www.kamailio.org/docs/modules/stable/modules/websocket.html) تغییر دهید.

فایل [kamailio.cfg](kamailio.cfg)

- آدرس سرور  کمیلیو:‌ در این حالت: 192.168.21.45
- پورت WebSocket (TCP): 80
- پورت‌های SIP (TCP/UDP): 5060 (برای اتصالات استاندارد SIP)

اطمینان حاصل کنید که سرور Kamailio برای اتصالات WebSocket روی پورت مشخص‌شده به درستی تنظیم شده باشد.

## پیاده‌سازی‌های کلاینت SIP
- کلاینت [sip_client.py](sip_client.py): کلاینت SIP که به ازای هر اجرا یک تماس برقرار می‌کند.

## نحوه استفاده از کلاینت SIP
### گزینه‌های خط فرمان

- گزینه `--username`: نام کاربری SIP برای ثبت‌نام و شروع تماس‌ها. (اختیاری، پیش‌فرض: "1100")
- گزینه`--send_bye`: فلگ برای تعیین ارسال پیام BYE پس از تماس. (اختیاری، پیش‌فرض: "True")
- گزینه`--invite_mode`: فلگ برای فعال کردن حالت INVITE برای برقراری تماس. (اختیاری، پیش‌فرض: "False")
- گزینه`--callee_number`: شماره مخاطب برای پیام INVITE. (اختیاری، پیش‌فرض: None)
- گزینه `--connection_type` نحوه اتصال. tcp/ws/udp (اختیاری، حالت پیش فرض: tcp)

### مثال استفاده

برای اجرای کلاینت SIP، می‌توانید از مثال‌های زیر استفاده کنید: (در این حالت برنامه با شماره 1200 رجیستر می‌کند و به 1001 زنگ میزند)
`python3 sip_client.py --send_bye True --username 1200 --invite_mode True --callee_number 1001 --connection_type ws`
یا اجرای ساده با مقادیر پیش‌فرض:
`python3 sip_client.py`


### کارهای آینده

- پشتیبانی از NAT: در پیاده‌سازی فعلی هنگام کار در پشت NAT مشکلاتی وجود دارد که باید برای ارتباط درست در این محیط‌ها حل شود.
