; هذا الملف هو سكريبت لبرنامج Inno Setup
; يقوم بإنشاء برنامج تثبيت (setup.exe) لتطبيق بايثون الذي تم تجميعه بواسطة PyInstaller

[Setup]
; معلومات التطبيق الأساسية
AppName=ARABLY ERP System
AppVersion=1.0
AppPublisher=Your Company Name
AppPublisherURL=http://www.yourcompany.com/
AppSupportURL=http://www.yourcompany.com/
AppUpdatesURL=http://www.yourcompany.com/

; مسار التثبيت الافتراضي في مجلد Program Files
DefaultDirName={autopf}\ARABLY ERP System

; ملف اتفاقية الترخيص الذي سيظهر للمستخدم
LicenseFile=license.txt

; ملف "اقرأني" الذي سيظهر بعد اكتمال التثبيت
InfoAfterFile=readme.txt

; اسم مجلد التطبيق في قائمة ابدأ
DefaultGroupName=ARABLY ERP System

; اسم ملف التثبيت الناتج
OutputBaseFilename=ARABLY_ERP_Setup

; مكان حفظ ملف التثبيت الناتج
OutputDir=installer_output

; إعدادات الضغط لتحسين حجم الملف
Compression=lzma
SolidCompression=yes

; تصميم معالج التثبيت
WizardStyle=modern

; طلب صلاحيات المدير عند التشغيل
PrivilegesRequired=admin

[Languages]
Name: "arabic"; MessagesFile: "compiler:Languages\Arabic.isl"

[Tasks]
; إضافة خيار لإنشاء أيقونة على سطح المكتب
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; هذا هو الجزء الأهم: يحدد الملفات التي سيتم تضمينها في برنامج التثبيت
; يقوم بنسخ كل محتويات المجلد الذي أنشأه PyInstaller
Source: "dist\ARABLY_ERP\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; إنشاء أيقونة في قائمة ابدأ
Name: "{group}\ARABLY ERP System"; Filename: "{app}\ARABLY_ERP.exe"
; إنشاء أيقونة على سطح المكتب إذا اختار المستخدم ذلك
Name: "{autodesktop}\ARABLY ERP System"; Filename: "{app}\ARABLY_ERP.exe"; Tasks: desktopicon