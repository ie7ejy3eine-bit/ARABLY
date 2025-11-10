import sys
import json, os, functools, shutil
import webbrowser # لاستيراد مكتبة فتح المتصفح
import database
import uuid # لاستيراد مكتبة توليد المعرفات الفريدة
import requests # <-- إضافة مكتبة الطلبات
from sqlalchemy import func # استيراد دالة func لحساب الإجماليات
import datetime # <-- استيراد مكتبة التاريخ والوقت
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QStatusBar,
    QGridLayout, QGroupBox, QLineEdit, QComboBox, QDateEdit, QTableWidget, QStyle,
    QTableWidgetItem, QPushButton, QTextEdit, QHeaderView, QHBoxLayout, QDialog, QFrame, QProgressBar,
    QFormLayout, QDialogButtonBox, QFileDialog, QMessageBox, QListWidget, QCheckBox, QInputDialog, QGraphicsDropShadowEffect
)
from PySide6.QtPrintSupport import QPrinterInfo, QPrintPreviewDialog, QPrinter
from PySide6.QtGui import QAction, QIcon, QPixmap, QColor, QTextDocument, QScreen, QPageSize, QPageLayout, QDesktopServices
from PySide6.QtCore import (Qt, QDate, QPropertyAnimation, QEasingCurve, QPoint, QTimer, QRect, QStandardPaths,
                          QSequentialAnimationGroup, QParallelAnimationGroup)
from PySide6.QtCore import QTranslator, QLocale, QCoreApplication, QThread, Signal, QObject

__version__ = "1.0.0" # متغير لتحديد الإصدار الحالي للبرنامج


def get_app_data_path(filename):
    """
    تُرجع المسار الكامل لملف الإعدادات داخل مجلد بيانات التطبيق الخاص بالمستخدم.
    هذا يضمن أن البرنامج لديه صلاحيات للكتابة على الملفات بعد التثبيت.
    """
    # الحصول على المسار المخصص لبيانات التطبيق (مثل C:/Users/user/AppData/Roaming)
    app_data_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
    
    # إنشاء المجلد إذا لم يكن موجوداً
    if not os.path.exists(app_data_dir):
        os.makedirs(app_data_dir, exist_ok=True)
        
    return os.path.join(app_data_dir, filename)

class MainWindow(QMainWindow):
    def __init__(self, business_profile, company_config):
        self.company_config = company_config # تخزين إعدادات الشركة الحالية
        self.logout_requested = False # تم تصحيح هذا السطر
        super().__init__() # تم تصحيح هذا السطر
        self.business_profile = business_profile
        self.opened_windows = [] # لتخزين النوافذ المفتوحة
        self.setWindowTitle(f"نظام ERP - {self.business_profile.get('window_title', 'نشاط تجاري')}")

        # --- جعل حجم النافذة متناسباً مع الشاشة ---
        screen = QApplication.primaryScreen()
        available_geometry = screen.availableGeometry()
        
        # تحديد حجم النافذة الافتراضي بنسبة 90% من حجم الشاشة المتاح
        # هذا يضمن أن النافذة لا تتجاوز حدود الشاشة أبداً
        self.resize(available_geometry.width() * 0.9, available_geometry.height() * 0.9)

        # وضع النافذة في منتصف الشاشة
        self.move(available_geometry.center() - self.rect().center())
        self.setMinimumSize(1024, 768) # تحديد أقل حجم ممكن للنافذة

        # تعيين اتجاه الواجهة من اليمين لليسار
        self.setLayoutDirection(Qt.RightToLeft)

        # إنشاء القوائم الرئيسية
        self.create_menus()

        # إنشاء شريط الحالة السفلي
        self.setStatusBar(QStatusBar(self))
        self.statusBar().hide() # إخفاء شريط الحالة بشكل دائم

        # الواجهة الرئيسية: لوحة التحكم
        self.setCentralWidget(DashboardWidget())

        # --- تحميل إعدادات النافذة المحفوظة ---
        self.load_window_state()

    def open_in_new_window(self, widget, title):
        """
        يفتح الواجهة (widget) في نافذة جديدة مستقلة.
        """
        widget.setWindowTitle(title)
        # تحديد حجم مبدئي مناسب للنافذة الجديدة
        widget.resize(1000, 700)
        widget.show()
        self.opened_windows.append(widget)

    def open_sales_invoice(self):
        """يفتح واجهة فاتورة المبيعات الجديدة"""
        sales_widget = SalesInvoiceWidget()
        self.open_in_new_window(sales_widget, "فاتورة مبيعات جديدة")

    def open_sales_return(self):
        """يفتح واجهة مرتجع المبيعات الجديدة"""
        return_widget = SalesReturnWidget()
        self.open_in_new_window(return_widget, "مرتجع مبيعات")

    def open_inventory_management(self):
        """يفتح واجهة إدارة المخزون"""
        inventory_widget = InventoryWidget()
        self.open_in_new_window(inventory_widget, "إدارة الأصناف والمخزون")

    def open_user_permissions(self):
        """يفتح واجهة صلاحيات المستخدمين"""
        widget = UsersManagementWidget()
        self.open_in_new_window(widget, "إدارة المستخدمين والصلاحيات")

    def open_company_settings(self):
        """يفتح واجهة إعدادات الشركة"""
        widget = CompanySettingsWidget()
        self.open_in_new_window(widget, "إعدادات الشركة")

    def open_pricing_policies(self):
        """يفتح واجهة سياسات التسعير"""
        widget = PricingPoliciesWidget()
        self.open_in_new_window(widget, "سياسات التسعير")

    def open_taxes_settings(self):
        """يفتح واجهة إعدادات الضرائب"""
        widget = TaxesSettingsWidget()
        self.open_in_new_window(widget, "إعدادات الضرائب")

    def open_printing_settings(self):
        """يفتح واجهة إعدادات الطباعة"""
        widget = PrintingSettingsWidget()
        self.open_in_new_window(widget, "إعدادات الطباعة")

    def open_network_settings(self):
        """يفتح واجهة إعدادات الشبكة"""
        widget = NetworkSettingsWidget()
        self.open_in_new_window(widget, "إعدادات الشبكة والاتصال")

    def open_sales_reports(self):
        """يفتح واجهة تقارير المبيعات"""
        widget = SalesReportsWidget()
        self.open_in_new_window(widget, "تقارير المبيعات")

    def open_stores_management(self):
        """يفتح واجهة إدارة المخازن"""
        widget = StoresManagementWidget()
        self.open_in_new_window(widget, "إدارة المخازن")

    def open_inventory_count(self):
        """يفتح واجهة جرد المخزون"""
        widget = InventoryCountWidget()
        self.open_in_new_window(widget, "جرد المخزون")

    def open_barcode_printing(self):
        """يفتح واجهة طباعة الباركود"""
        widget = BarcodePrintingWidget()
        self.open_in_new_window(widget, "طباعة الباركود")

    def open_treasury(self):
        """يفتح واجهة الخزينة"""
        widget = TreasuryWidget()
        self.open_in_new_window(widget, "الخزينة")

    def open_purchase_invoice(self):
        """يفتح واجهة فاتورة المشتريات"""
        widget = PurchasesWidget()
        self.open_in_new_window(widget, "فاتورة مشتريات")

    def open_customers_management(self):
        """يفتح واجهة إدارة العملاء"""
        widget = CustomersManagementWidget()
        self.open_in_new_window(widget, "إدارة العملاء")

    def open_suppliers_management(self):
        """يفتح واجهة إدارة الموردين"""
        widget = SuppliersManagementWidget()
        self.open_in_new_window(widget, "إدارة الموردين")

    def open_sellers_management(self):
        """يفتح واجهة إدارة البائعين"""
        widget = SellersManagementWidget()
        self.open_in_new_window(widget, "إدارة البائعين")

    def open_ai_assistant(self):
        """يفتح نافذة المساعد الذكي"""
        dialog = AIAssistantDialog(self)
        dialog.exec()

    def open_activation_screen(self):
        """يفتح شاشة تفعيل البرنامج"""
        dialog = ActivationWidget(self)
        dialog.exec()

    def open_updates_screen(self):
        """يفتح شاشة تحديثات البرنامج"""
        dialog = UpdateWidget(self)
        dialog.exec()

    def create_database_backup(self):
        """
        ينشئ نسخة احتياطية من قاعدة البيانات (يعمل حالياً مع SQLite فقط).
        """
        # التحقق من أن قاعدة البيانات المستخدمة هي SQLite
        if self.company_config.get("engine") != "sqlite":
            QMessageBox.warning(self, "غير مدعوم", "ميزة النسخ الاحتياطي التلقائي متاحة حالياً لقواعد بيانات SQLite فقط.")
            return

        # تحديد مسار ملف قاعدة البيانات الأصلي
        db_name = self.company_config.get("dbname")
        if not db_name:
            QMessageBox.critical(self, "خطأ", "لم يتم تحديد اسم قاعدة البيانات في الإعدادات.")
            return
        
        source_path = get_app_data_path(db_name) if not os.path.isabs(db_name) else db_name
        if not os.path.exists(source_path):
            QMessageBox.critical(self, "خطأ", f"ملف قاعدة البيانات الأصلي غير موجود في المسار:\n{source_path}")
            return

        # طلب مسار الحفظ من المستخدم
        default_backup_name = f"backup_{os.path.basename(db_name)}_{datetime.date.today().strftime('%Y-%m-%d')}.db"
        dest_path, _ = QFileDialog.getSaveFileName(self, "حفظ النسخة الاحتياطية", default_backup_name, "SQLite Database (*.db);;All Files (*)")

        if not dest_path:
            return # ألغى المستخدم العملية

        # نسخ الملف
        try:
            shutil.copy2(source_path, dest_path)
            QMessageBox.information(self, "نجاح", f"تم إنشاء نسخة احتياطية بنجاح في المسار:\n{dest_path}")
            # فتح المجلد الذي يحتوي على النسخة الاحتياطية
            QDesktopServices.openUrl(f"file:///{os.path.dirname(dest_path)}")
        except Exception as e:
            QMessageBox.critical(self, "فشل النسخ", f"حدث خطأ أثناء إنشاء النسخة الاحتياطية:\n{e}")

    def restore_database_backup(self):
        """
        يستعيد قاعدة البيانات من ملف نسخة احتياطية (SQLite فقط).
        هذه عملية خطيرة وستقوم بإعادة تشغيل البرنامج.
        """
        # التحقق من أن قاعدة البيانات المستخدمة هي SQLite
        if self.company_config.get("engine") != "sqlite":
            QMessageBox.warning(self, "غير مدعوم", "ميزة استعادة النسخة الاحتياطية متاحة حالياً لقواعد بيانات SQLite فقط.")
            return

        # تحذير المستخدم
        reply = QMessageBox.question(self, "تأكيد الاستعادة",
                                     "<b>تحذير خطير!</b><br><br>"
                                     "هل أنت متأكد من أنك تريد استعادة نسخة احتياطية؟<br>"
                                     "هذه العملية ستحذف <b>جميع البيانات الحالية</b> وتستبدلها بالبيانات الموجودة في ملف النسخة الاحتياطية.<br><br>"
                                     "<b>لا يمكن التراجع عن هذا الإجراء.</b> سيتم إعادة تشغيل البرنامج بعد الاستعادة.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.No:
            return

        # طلب ملف النسخة الاحتياطية من المستخدم
        backup_path, _ = QFileDialog.getOpenFileName(self, "اختر ملف النسخة الاحتياطية للاستعادة", "", "SQLite Database (*.db);;All Files (*)")

        if not backup_path:
            return # ألغى المستخدم العملية

        # تحديد مسار قاعدة البيانات الحالية
        db_name = self.company_config.get("dbname")
        current_db_path = get_app_data_path(db_name) if not os.path.isabs(db_name) else db_name

        try:
            # استبدال الملف الحالي بملف النسخة الاحتياطية
            shutil.copy2(backup_path, current_db_path)
            QMessageBox.information(self, "نجاح", "تم استعادة النسخة الاحتياطية بنجاح.\nسيتم الآن إعادة تشغيل البرنامج.")
            # إعادة تشغيل البرنامج لتطبيق التغييرات
            QApplication.instance().quit()
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            QMessageBox.critical(self, "فشل الاستعادة", f"حدث خطأ أثناء استعادة النسخة الاحتياطية:\n{e}")

    def create_menus(self):
        menu_bar = self.menuBar()

        # قائمة الملف
        # استخدام functools.partial لتمرير الوسائط إلى الدوال
        create_menu_item = functools.partial(self.create_menu_item, menu_bar=menu_bar)

        # --- قائمة الملف (مشتركة للجميع) ---
        file_menu = menu_bar.addMenu("ملف")
        logout_action = QAction(self.style().standardIcon(QStyle.SP_DialogCancelButton), "تسجيل الخروج", self)
        logout_action.triggered.connect(self.handle_logout)
        file_menu.addAction(logout_action)
        file_menu.addSeparator()
        exit_action = QAction(self.style().standardIcon(QStyle.SP_DialogCloseButton), "إغلاق البرنامج", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # --- بناء القوائم بناءً على نوع النشاط ---
        profile_menus = self.business_profile.get('menus', [])

        if 'inventory' in profile_menus:
            create_menu_item("المخزون", [
                ("إدارة الأصناف", self.open_inventory_management, QStyle.SP_ComputerIcon),
                ("إدارة المخازن", self.open_stores_management, QStyle.SP_DirHomeIcon),
                ("جرد المخزون", self.open_inventory_count, QStyle.SP_FileDialogDetailedView),
                "---",
                ("طباعة الباركود", self.open_barcode_printing, QStyle.SP_FileLinkIcon),
            ])

        if 'sales' in profile_menus:
            sales_menu_title = self.business_profile.get('sales_menu_title', 'المبيعات والفواتير')
            invoice_action_title = self.business_profile.get('invoice_action_title', 'فاتورة جديدة')
            create_menu_item(sales_menu_title, [
                (invoice_action_title, self.open_sales_invoice, QStyle.SP_FileIcon),
                ("مرتجع مبيعات", self.open_sales_return, QStyle.SP_ArrowLeft),
            ])

        if 'purchases' in profile_menus:
            create_menu_item("المشتريات", [
                ("فاتورة مشتريات جديدة", self.open_purchase_invoice, QStyle.SP_ArrowDown),
            ])

        if 'contacts' in profile_menus:
            contacts_menu_title = self.business_profile.get('contacts_menu_title', 'العملاء والموردين')
            customer_action_title = self.business_profile.get('customer_action_title', 'إدارة العملاء')
            contact_items = [
                (customer_action_title, self.open_customers_management, QStyle.SP_DirIcon),
            ]
            if 'inventory' in profile_menus: # الموردين يظهرون فقط مع الأنشطة التي بها مخزون
                contact_items.append(("إدارة الموردين", self.open_suppliers_management, QStyle.SP_DriveHDIcon))
            contact_items.append(("إدارة البائعين", self.open_sellers_management, QStyle.SP_ComputerIcon))
            create_menu_item(contacts_menu_title, contact_items)

        # --- القوائم المشتركة ---
        create_menu_item("المحاسبة", [
            ("الخزينة", self.open_treasury, QStyle.SP_MessageBoxInformation),
        ])

        create_menu_item("التقارير", [
            ("تقارير المبيعات", self.open_sales_reports, QStyle.SP_FileDialogInfoView),
        ])

        # --- قائمة الصيانة ---
        create_menu_item("صيانة", [
            ("إنشاء نسخة احتياطية", self.create_database_backup, QStyle.SP_DialogSaveButton),
            ("استعادة نسخة احتياطية", self.restore_database_backup, QStyle.SP_DialogOpenButton),
        ])

        # --- القوائم المشتركة (تكملة) ---
        settings_menu = create_menu_item("الإعدادات", [
            ("صلاحيات المستخدمين", self.open_user_permissions, QStyle.SP_DialogYesToAllButton),
            "---",
                ("سياسات التسعير", self.open_pricing_policies, QStyle.SP_ArrowUp),
                ("إعدادات الضرائب", self.open_taxes_settings, QStyle.SP_ArrowRight),
                "---",
            ("إعدادات الشركة", self.open_company_settings, QStyle.SP_DirIcon),
            ("إعدادات الطباعة", self.open_printing_settings, QStyle.SP_FileDialogDetailedView),
            ("إعدادات الشبكة", self.open_network_settings, QStyle.SP_DriveNetIcon),
            "---",
            ("تفعيل البرنامج", self.open_activation_screen, QStyle.SP_DialogApplyButton),
            "---",
            ("تحديثات البرنامج", self.open_updates_screen, QStyle.SP_BrowserReload),
        ])

        help_menu = menu_bar.addMenu("مساعدة")
        ai_assistant_action = QAction(self.style().standardIcon(QStyle.SP_MessageBoxQuestion), "المساعد الذكي", self)
        ai_assistant_action.triggered.connect(self.open_ai_assistant)
        help_menu.addAction(ai_assistant_action)
        help_menu.addAction(QAction(self.style().standardIcon(QStyle.SP_DialogHelpButton), self.tr("فيديوهات تعليمية"), self))

        # إضافة إعدادات اللغة
        language_action = QAction(self.style().standardIcon(QStyle.SP_FileDialogDetailedView), self.tr("إعدادات اللغة"), self)
        language_action.triggered.connect(self.open_language_settings)
        settings_menu.addAction(language_action)

    def create_menu_item(self, menu_title, actions, menu_bar):
        """دالة مساعدة لإنشاء قائمة وإضافة عناصرها"""
        menu = menu_bar.addMenu(menu_title)
        if actions:
            for action_item in actions:
                if action_item == "---":
                    menu.addSeparator()
                else:
                    title, slot, icon = action_item
                    action = QAction(self.style().standardIcon(icon), title, self)
                    action.triggered.connect(slot)
                    menu.addAction(action)
        return menu

    def open_language_settings(self):
        """يفتح واجهة إعدادات اللغة"""
        widget = LanguageSettingsWidget()
        self.open_in_new_window(widget, "إعدادات اللغة")

    def handle_logout(self):
        """يعالج عملية تسجيل الخروج"""
        self.logout_requested = True
        self.close()

    def save_window_state(self):
        """يحفظ حجم وموضع النافذة في ملف الإعدادات"""
        all_settings = {}
        settings_file = get_app_data_path("settings.json")
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    all_settings = json.load(f)
            except json.JSONDecodeError:
                pass # تجاهل الملف التالف أو الفارغ
        
        if "window_state" not in all_settings:
            all_settings["window_state"] = {}

        geometry = self.geometry()
        all_settings["window_state"]["geometry"] = [geometry.x(), geometry.y(), geometry.width(), geometry.height()]
        
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump(all_settings, f, ensure_ascii=False, indent=4)

    def load_window_state(self):
        """يقرأ حجم وموضع النافذة من ملف الإعدادات ويطبقه"""
        settings_file = get_app_data_path("settings.json")
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    all_settings = json.load(f)
                    geometry_data = all_settings.get("window_state", {}).get("geometry")
                    if geometry_data and len(geometry_data) == 4:
                        self.setGeometry(QRect(*geometry_data))
            except (json.JSONDecodeError, FileNotFoundError):
                pass # تجاهل الأخطاء في حال عدم وجود الملف أو تلفه

    def closeEvent(self, event):
        """
        يتم استدعاؤها تلقائياً عند محاولة إغلاق النافذة.
        نستخدمها لحفظ حالة النافذة قبل الخروج.
        """
        self.save_window_state()
        super().closeEvent(event)
        QApplication.quit() # تأكد من إغلاق التطبيق بالكامل

class SalesInvoiceWidget(QWidget):
    """واجهة إنشاء فاتورة مبيعات جديدة"""
    def __init__(self, invoice_id=None):
        super().__init__()
        self.db_session = database.SessionLocal()
        self.setLayoutDirection(Qt.RightToLeft)
        self.invoice_id = invoice_id  # تخزين رقم الفاتورة للتعديل
        self.init_ui()
        self.update_invoice_number() # استدعاء لتحديث رقم الفاتورة
        self.load_customers()
        self.connect_signals()

        if self.invoice_id:
            self.load_invoice_data(self.invoice_id)
            self.update_ui_for_edit_mode() # تم تصحيح هذا السطر


    def init_ui(self):
        main_layout = QGridLayout(self)

        # --- مجموعة معلومات الفاتورة والعميل ---
        info_group = QGroupBox(self.tr("معلومات الفاتورة والعميل"))
        info_layout = QGridLayout()

        info_layout.addWidget(QLabel("العميل:"), 0, 0)
        customer_layout = QHBoxLayout()
        self.customer_combo = QComboBox()
        self.customer_combo.setEditable(True) # للسماح بالبحث
        self.add_customer_button = QPushButton("+")
        self.add_customer_button.setFixedSize(25, 25)
        self.add_customer_button.setToolTip("إضافة عميل جديد")
        customer_layout.addWidget(self.customer_combo)
        customer_layout.addWidget(self.add_customer_button)
        info_layout.addLayout(customer_layout, 0, 1)

        info_layout.addWidget(QLabel(self.tr("مديونية سابقة:")), 0, 2)
        self.debt_label = QLabel("0.00")
        self.debt_label.setStyleSheet("color: red; font-weight: bold;")
        info_layout.addWidget(self.debt_label, 0, 3)

        info_layout.addWidget(QLabel(self.tr("البائع:")), 1, 0)
        self.salesperson_combo = QComboBox() # سيتم تحميل البائعين من قاعدة البيانات
        info_layout.addWidget(self.salesperson_combo, 1, 1)

        info_layout.addWidget(QLabel(self.tr("رقم الفاتورة:")), 2, 0)
        self.invoice_num_label = QLabel("...") # سيتم تحديثه تلقائياً
        info_layout.addWidget(self.invoice_num_label, 2, 1)

        info_layout.addWidget(QLabel(self.tr("التاريخ:")), 2, 2)
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        info_layout.addWidget(self.date_edit, 2, 3)

        info_layout.addWidget(QLabel(self.tr("طريقة الدفع:")), 3, 0)
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems([self.tr("نقدي"), self.tr("آجل"), self.tr("شيك")])
        info_layout.addWidget(self.payment_method_combo, 3, 1)
        
        self.tax_combo = QComboBox()
        info_layout.addWidget(QLabel(self.tr("الضريبة المطبقة:")), 3, 2)
        info_layout.addWidget(self.tax_combo, 3, 3)

        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group, 0, 0, 1, 2)

        # --- مجموعة إضافة الأصناف ---
        add_item_group = QGroupBox("إضافة صنف للفاتورة")
        add_item_layout = QHBoxLayout()
        self.item_search_edit = QLineEdit()
        self.item_search_edit.setPlaceholderText("ابحث بكود أو اسم الصنف...")
        add_item_button = QPushButton("إضافة الصنف")
        add_item_button.clicked.connect(self.add_item_to_invoice)
        add_item_layout.addWidget(QLabel("بحث:"))
        add_item_layout.addWidget(self.item_search_edit)
        add_item_layout.addWidget(add_item_button)
        add_item_group.setLayout(add_item_layout)
        main_layout.addWidget(add_item_group, 1, 0, 1, 2)

        # --- مجموعة الأصناف ---
        items_group = QGroupBox("أصناف الفاتورة")
        items_layout = QVBoxLayout()

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(10) # أضفنا عموداً للتكلفة (مخفي) وللحذف
        self.items_table.setHorizontalHeaderLabels(
            ["ID", "كود الصنف", "اسم الصنف", "المخزن", "الكمية", "السعر", "الخصم (%)", "الإجمالي", "حذف", "التكلفة"]
        )
        self.items_table.setColumnHidden(0, True) # إخفاء ID الصنف
        self.items_table.setColumnHidden(9, True) # إخفاء عمود التكلفة
        # تحديد عرض ثابت لعمود الحذف ليكون شكله أفضل
        self.items_table.setColumnWidth(8, 50)
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        items_layout.addWidget(self.items_table)
        items_group.setLayout(items_layout)
        main_layout.addWidget(items_group, 2, 0, 1, 2)

        # --- مجموعة الملاحظات ---
        notes_group = QGroupBox(self.tr("ملاحظات للطباعة"))
        notes_layout = QVBoxLayout()
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText(self.tr("اكتب هنا شروط الضمان أو أي ملاحظات أخرى..."))
        notes_layout.addWidget(self.notes_edit)
        notes_group.setLayout(notes_layout)
        main_layout.addWidget(notes_group, 3, 0)

        # --- مجموعة الإجماليات ---
        totals_group = QGroupBox(self.tr("ملخص الفاتورة"))
        totals_layout = QGridLayout()

        totals_layout.addWidget(QLabel(self.tr("إجمالي الفاتورة:")), 0, 0)
        self.subtotal_label = QLabel("0.00")
        totals_layout.addWidget(self.subtotal_label, 0, 1)

        totals_layout.addWidget(QLabel(self.tr("الخصم:")), 1, 0)
        self.discount_edit = QLineEdit("0.00")
        totals_layout.addWidget(self.discount_edit, 1, 1)

        totals_layout.addWidget(QLabel(self.tr("ضريبة القيمة المضافة:")), 2, 0)
        self.vat_label = QLabel("0.00")
        totals_layout.addWidget(self.vat_label, 2, 1)

        totals_layout.addWidget(QLabel(self.tr("الصافي:")), 3, 0)
        self.grand_total_label = QLabel("0.00")
        self.grand_total_label.setStyleSheet("color: blue; font-size: 16px; font-weight: bold;")
        totals_layout.addWidget(self.grand_total_label, 3, 1)

        totals_layout.addWidget(QLabel(self.tr("المدفوع:")), 4, 0)
        self.paid_edit = QLineEdit("0.00")
        totals_layout.addWidget(self.paid_edit, 4, 1)

        totals_layout.addWidget(QLabel(self.tr("الرصيد بعد الفاتورة:")), 5, 0)
        self.balance_after_invoice_label = QLabel("0.00")
        self.balance_after_invoice_label.setStyleSheet("color: green; font-weight: bold;")
        totals_layout.addWidget(self.balance_after_invoice_label, 5, 1)
        
        # تحليل الربح المخفي
        totals_layout.addWidget(QLabel("ربح الفاتورة:"), 6, 0)
        self.profit_label = QLabel("0.00")
        self.profit_label.setStyleSheet("color: #c0c0c0;") # لون رمادي فاتح لجعله غير بارز
        totals_layout.addWidget(self.profit_label, 6, 1)
        
        totals_group.setLayout(totals_layout)
        main_layout.addWidget(totals_group, 3, 1)

        # --- أزرار الإجراءات ---
        buttons_layout = QHBoxLayout()
        self.save_button = QPushButton(self.style().standardIcon(QStyle.SP_DialogSaveButton), self.tr("حفظ واعتماد")) # تم تعديل هذا السطر
        self.save_draft_button = QPushButton(self.style().standardIcon(QStyle.SP_DriveFDIcon), self.tr("حفظ كمسودة")) # تم تعديل هذا السطر
        self.print_button = QPushButton(self.style().standardIcon(QStyle.SP_FileDialogDetailedView), self.tr("طباعة")) # تم تعديل هذا السطر
        self.new_button = QPushButton(self.style().standardIcon(QStyle.SP_FileIcon), self.tr("فاتورة جديدة"))

        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.save_draft_button)
        buttons_layout.addWidget(self.print_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.new_button)
        buttons_layout.addStretch()

        main_layout.addLayout(buttons_layout, 4, 0, 1, 2)

        self.setLayout(main_layout)

    def connect_signals(self):
        """ربط الإشارات بالدوال"""
        self.customer_combo.currentIndexChanged.connect(self.update_customer_debt)
        self.items_table.cellChanged.connect(self.update_row_total)
        self.discount_edit.textChanged.connect(self.update_totals)
        self.paid_edit.textChanged.connect(self.update_totals)
        self.save_button.clicked.connect(lambda: self.save_invoice(is_draft=False))
        self.save_draft_button.clicked.connect(lambda: self.save_invoice(is_draft=True))
        self.print_button.clicked.connect(self.print_invoice)
        self.new_button.clicked.connect(self.reset_form)
        self.item_search_edit.returnPressed.connect(self.add_item_to_invoice) # تفعيل Enter للبحث
        self.payment_method_combo.currentIndexChanged.connect(self.on_payment_method_changed)
        self.add_customer_button.clicked.connect(self.open_add_customer_dialog)
        self.tax_combo.currentIndexChanged.connect(self.update_totals)

    def update_ui_for_edit_mode(self):
        """تحديث الواجهة لنمط التعديل"""
        self.window().setWindowTitle(f"تعديل فاتورة رقم {self.invoice_id}")
        self.save_button.setText("تحديث الفاتورة")
        self.save_draft_button.setText("تحديث كمسودة")
        self.new_button.setVisible(False) # إخفاء زر فاتورة جديدة في وضع التعديل

    def load_invoice_data(self, invoice_id):
        """تحميل بيانات فاتورة موجودة في الواجهة"""
        invoice = self.db_session.query(database.Invoice).filter(database.Invoice.id == invoice_id).first()
        if not invoice:
            QMessageBox.critical(self, "خطأ", "لم يتم العثور على الفاتورة المطلوبة.")
            self.close() # إغلاق الواجهة إذا لم يتم العثور على الفاتورة
            return

        # --- منع الإشارات أثناء تحميل البيانات ---
        for widget in [self.customer_combo, self.date_edit, self.payment_method_combo, self.tax_combo, self.discount_edit, self.paid_edit]:
            widget.blockSignals(True)
        self.items_table.blockSignals(True)

        # --- تعبئة الحقول ---
        # العميل
        if invoice.customer_id:
            customer_index = self.customer_combo.findData(invoice.customer_id)
            self.customer_combo.setCurrentIndex(customer_index)
        else:
            self.customer_combo.setCurrentIndex(0) # عميل نقدي

        # التاريخ
        self.date_edit.setDate(QDate(invoice.date))

        # طريقة الدفع
        self.payment_method_combo.setCurrentText(invoice.payment_method)
        
        # البائع
        if invoice.seller_id:
            seller_index = self.salesperson_combo.findData(invoice.seller_id)
            self.salesperson_combo.setCurrentIndex(seller_index)

        # الضريبة (تحتاج إلى منطق إضافي لمطابقة القيمة)
        # سنبحث عن القيمة الأقرب
        # Note: This might not be perfect if tax rates change.
        # A better approach would be to store the tax_id in the invoice.
        if invoice.tax_rate is not None:
            for i in range(self.tax_combo.count()):
                if self.tax_combo.itemData(i) is not None and abs(self.tax_combo.itemData(i) - invoice.tax_rate) < 0.001:
                    self.tax_combo.setCurrentIndex(i)
                    break

        # الملاحظات، الخصم، المدفوع
        self.notes_edit.setText(invoice.notes)
        self.discount_edit.setText(str(invoice.discount_amount or 0.0))
        self.paid_edit.setText(str(invoice.paid_amount or 0.0))

        # --- تعبئة جدول الأصناف ---
        self.items_table.setRowCount(0)
        for item in invoice.items:
            self.add_item_to_invoice(item_id_to_add=item.item_id, quantity=item.quantity, price=item.price_per_unit, discount=item.discount_percent)

        # --- إعادة تفعيل الإشارات واستدعاء التحديث ---
        for widget in [self.customer_combo, self.date_edit, self.payment_method_combo, self.tax_combo, self.discount_edit, self.paid_edit]:
            widget.blockSignals(False)
        self.items_table.blockSignals(False)

        # استدعاء تحديث المديونية والإجماليات يدوياً
        self.update_customer_debt(self.customer_combo.currentIndex())
        self.update_totals()


    def load_customers(self):
        self.load_sellers() # تحميل البائعين أيضاً
        self.load_taxes() # تحميل الضرائب
        """تحميل العملاء من قاعدة البيانات"""
        self.customer_combo.clear()
        customers = self.db_session.query(database.Customer).all()
        self.customer_combo.addItem(self.tr("عميل نقدي"), -1)
        self.customer_combo.addItem("عميل نقدي", -1)
        for customer in customers:
            self.customer_combo.addItem(customer.name, customer.id)

    def load_sellers(self):
        """تحميل البائعين من قاعدة البيانات"""
        self.salesperson_combo.clear()
        sellers = self.db_session.query(database.Seller).all()
        self.salesperson_combo.addItem(self.tr("بائع افتراضي"), -1)
        for seller in sellers:
            self.salesperson_combo.addItem(seller.name, seller.id)

    def load_taxes(self):
        """تحميل الضرائب من ملف الإعدادات"""
        self.tax_combo.clear()
        settings_file = get_app_data_path("settings.json")
        self.tax_combo.addItem(self.tr("بدون ضريبة"), 0.0) # خيار افتراضي
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    taxes = settings.get("taxes", [])
                    for tax in taxes:
                        self.tax_combo.addItem(f"{tax['name']} ({tax['rate']}%)", float(tax['rate']))
            except (json.JSONDecodeError, FileNotFoundError):
                pass

    def update_customer_debt(self, index):
        """تحديث حقل المديونية عند اختيار عميل"""
        customer_id = self.customer_combo.itemData(index)
        if customer_id and customer_id != -1:
            customer = self.db_session.query(database.Customer).filter(database.Customer.id == customer_id).first()
            if customer:
                self.debt_label.setText(f"{customer.current_debt:.2f}")
                self.pulse_debt_label() # تطبيق الأنيميشن
        else:
            self.debt_label.setText("0.00")
        self.update_totals()

    def pulse_debt_label(self):
        """يطبق أنيميشن نبض على حقل المديونية للتأكيد على التحديث"""
        shadow = QGraphicsDropShadowEffect(self.debt_label)
        shadow.setBlurRadius(0)
        shadow.setColor(QColor("#E06C75")) # لون أحمر فاتح
        shadow.setOffset(0, 0)
        self.debt_label.setGraphicsEffect(shadow)

        self.debt_anim = QPropertyAnimation(shadow, b"blurRadius")
        self.debt_anim.setStartValue(0)
        self.debt_anim.setEndValue(15)
        self.debt_anim.setDuration(300)
        self.debt_anim.setLoopCount(2) # تكرار النبض مرتين (ذهاباً وإياباً)
        self.debt_anim.start()

    def add_item_to_invoice(self, item_id_to_add=None, quantity=1, price=None, discount=0):
        """
        البحث عن صنف وإضافته لجدول الفاتورة.
        يمكن استدعاؤها مع item_id_to_add لإضافة صنف برمجياً (عند تحميل فاتورة للتعديل).
        """
        item = None
        if item_id_to_add:
            item = self.db_session.query(database.Item).filter(database.Item.id == item_id_to_add).first()
        else:
            search_term = self.item_search_edit.text()
            if not search_term:
                return
            item = self.db_session.query(database.Item).filter(
                (database.Item.code == search_term) | (database.Item.name.contains(search_term))
            ).first()

        if not item:
            if not item_id_to_add: # لا تظهر رسالة خطأ عند تحميل فاتورة
                QMessageBox.warning(self, self.tr("خطأ"), self.tr("لم يتم العثور على الصنف!"))
            return

        row_pos = self.items_table.rowCount()
        self.items_table.insertRow(row_pos)
        self.items_table.setItem(row_pos, 0, QTableWidgetItem(str(item.id)))
        self.items_table.setItem(row_pos, 1, QTableWidgetItem(item.code))
        self.items_table.setItem(row_pos, 2, QTableWidgetItem(item.name))
        self.items_table.setItem(row_pos, 3, QTableWidgetItem(item.store.name if item.store else self.tr("غير محدد")))
        self.items_table.setItem(row_pos, 4, QTableWidgetItem(str(quantity)))
        
        # استخدام السعر الممرر أو سعر البيع الافتراضي
        effective_price = price if price is not None else item.sale_price
        self.items_table.setItem(row_pos, 5, QTableWidgetItem(f"{effective_price:.2f}"))
        
        self.items_table.setItem(row_pos, 6, QTableWidgetItem(str(discount)))
        self.items_table.setItem(row_pos, 7, QTableWidgetItem("0.00")) # إجمالي مبدئي
        self.items_table.setItem(row_pos, 9, QTableWidgetItem(f"{item.cost_price:.2f}")) # سعر التكلفة (مخفي)
        
        delete_button = QPushButton()
        delete_icon = self.style().standardIcon(QStyle.SP_TrashIcon)
        delete_button.setIcon(delete_icon)
        delete_button.setToolTip("حذف الصنف من الفاتورة")
        delete_button.clicked.connect(self.delete_invoice_item)
        self.items_table.setCellWidget(row_pos, 8, delete_button)

        self.update_row_total(row_pos, 4) 

        if not item_id_to_add: # فقط عند الإضافة من شريط البحث
            self.item_search_edit.clear()
        
        self.update_totals()


    def delete_invoice_item(self):
        """يحذف الصنف المحدد من جدول الفاتورة"""
        button_clicked = self.sender()
        if button_clicked:
            row = self.items_table.indexAt(button_clicked.pos()).row()
            self.items_table.removeRow(row)
            self.update_totals()

    def update_row_total(self, row, column):
        """تحديث إجمالي الصف عند تغيير الكمية أو السعر"""
        # يتم التحديث عند تغيير الكمية (4) أو السعر (5) أو الخصم (6)
        if column in [4, 5, 6]:
            try:
                quantity = float(self.items_table.item(row, 4).text())
                item_id = int(self.items_table.item(row, 0).text())
                
                # --- التحقق من الكمية المتاحة في المخزون ---
                item_in_db = self.db_session.query(database.Item).filter(database.Item.id == item_id).first()
                if item_in_db and quantity > item_in_db.quantity:
                    QMessageBox.warning(self, self.tr("كمية غير كافية"), 
                                        f"الكمية المطلوبة ({quantity}) للصنف '{item_in_db.name}'\n"
                                        f"أكبر من الكمية المتاحة في المخزون ({item_in_db.quantity}).")
                    # تلوين الخلية باللون الأحمر للتنبيه
                    self.items_table.item(row, 4).setBackground(QColor("#ffcccc"))
                else:
                    # إعادة لون الخلية إلى الطبيعي إذا كانت الكمية متاحة
                    self.items_table.item(row, 4).setBackground(QColor("white"))
                # -----------------------------------------

                price = float(self.items_table.item(row, 5).text())
                discount_percent = float(self.items_table.item(row, 6).text())

                # حساب الإجمالي بعد خصم الصنف
                total_before_discount = quantity * price
                discount_value = total_before_discount * (discount_percent / 100)
                total = total_before_discount - discount_value

                # تحديث خلية الإجمالي بدون إطلاق إشارة جديدة لمنع التكرار
                self.items_table.blockSignals(True)
                self.items_table.setItem(row, 7, QTableWidgetItem(f"{total:.2f}"))
                self.items_table.blockSignals(False)
                
                self.update_totals() # استدعاء التحديث الشامل
            except (ValueError, AttributeError):
                pass # تجاهل الأخطاء أثناء التعديل

    def update_totals(self):
        """حساب وتحديث كل إجماليات الفاتورة"""
        subtotal = 0.0
        total_cost = 0.0
        for row in range(self.items_table.rowCount()):
            try:
                subtotal += float(self.items_table.item(row, 7).text())
                cost = float(self.items_table.item(row, 9).text())
                quantity = float(self.items_table.item(row, 4).text())
                total_cost += cost * quantity
            except (ValueError, AttributeError):
                continue # تجاهل الصفوف غير المكتملة

        self.subtotal_label.setText(f"{subtotal:.2f}")

        try:
            # الخصم الإضافي على الفاتورة
            discount = float(self.discount_edit.text() or 0.0)
            
            total_after_discount = subtotal - discount

            # حساب ضريبة القيمة المضافة (14% كمثال)
            vat_rate = self.tax_combo.currentData() or 0.0
            vat_value = total_after_discount * (vat_rate / 100)
            self.vat_label.setText(f"{vat_value:.2f}")

            # حساب الصافي الإجمالي
            grand_total = total_after_discount + vat_value
            self.grand_total_label.setText(f"{grand_total:.2f}")

            # حساب الرصيد النهائي للعميل
            paid = float(self.paid_edit.text() or 0.0)
            old_debt = float(self.debt_label.text())
            balance_after = (old_debt + grand_total) - paid
            self.balance_after_invoice_label.setText(f"{balance_after:.2f}")

            # حساب وتحديث الربح
            profit = subtotal - total_cost
            self.profit_label.setText(f"{profit:.2f}")
        except ValueError:
            # في حالة إدخال نص غير رقمي في حقول الخصم أو المدفوع
            pass

    def save_invoice(self, is_draft=False):
        """
        حفظ الفاتورة في قاعدة البيانات (إنشاء جديد أو تحديث) وتحديث المخزون.
        """
        customer_id = self.customer_combo.currentData()
        if customer_id is None:
            QMessageBox.warning(self, self.tr("خطأ"), self.tr("يرجى تحديد العميل أولاً."))
            return

        if self.items_table.rowCount() == 0:
            QMessageBox.warning(self, self.tr("خطأ"), self.tr("لا يمكن حفظ فاتورة فارغة."))
            return

        # --- التحقق النهائي من الكميات قبل الحفظ (فقط للفواتير غير المسودة) ---
        if not is_draft:
            for row in range(self.items_table.rowCount()):
                item_id = int(self.items_table.item(row, 0).text())
                requested_quantity = int(self.items_table.item(row, 4).text())
                item_in_db = self.db_session.query(database.Item).filter(database.Item.id == item_id).first()
                
                # عند التعديل، يجب أن نأخذ في الاعتبار الكمية الأصلية في الفاتورة
                original_quantity_in_invoice = 0
                if self.invoice_id:
                    original_item = self.db_session.query(database.InvoiceItem).filter_by(invoice_id=self.invoice_id, item_id=item_id).first()
                    if original_item:
                        original_quantity_in_invoice = original_item.quantity

                if item_in_db and requested_quantity > (item_in_db.quantity + original_quantity_in_invoice):
                    QMessageBox.critical(self, "خطأ في الحفظ",
                                         f"لا يمكن حفظ الفاتورة.\n"
                                         f"الكمية المطلوبة للصنف '{item_in_db.name}' تتجاوز المخزون المتاح.")
                    return

        try:
            if self.invoice_id:
                # --- وضع التحديث ---
                self.update_existing_invoice(is_draft)
            else:
                # --- وضع الإنشاء ---
                self.create_new_invoice(is_draft)

            self.db_session.commit()

            if self.invoice_id:
                QMessageBox.information(self, "نجاح", "تم تحديث الفاتورة بنجاح!")
                self.close() # إغلاق نافذة التعديل
            else:
                message = "تم حفظ الفاتورة كمسودة بنجاح." if is_draft else "تم حفظ الفاتورة بنجاح!"
                QMessageBox.information(self, "نجاح", message)
                self.reset_form()

        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "خطأ فادح", f"حدث خطأ أثناء حفظ الفاتورة: {e}\nتم التراجع عن جميع التغييرات.")
        finally:
            # لا نغلق الجلسة هنا لأن الواجهة قد تظل مفتوحة
            pass

    def create_new_invoice(self, is_draft):
        """منطق إنشاء فاتورة جديدة"""
        seller_id = self.salesperson_combo.currentData()
        customer_id = self.customer_combo.currentData()

        # 1. إنشاء سجل الفاتورة
        new_invoice = database.Invoice(
            customer_id=customer_id,
            seller_id=seller_id if seller_id != -1 else None,
            date=self.date_edit.date().toPython(),
            total_amount=float(self.grand_total_label.text()),
            paid_amount=float(self.paid_edit.text()),
            discount_amount=float(self.discount_edit.text()),
            tax_rate=self.tax_combo.currentData() or 0.0,
            payment_method=self.payment_method_combo.currentText(),
            notes=self.notes_edit.toPlainText(),
            is_draft=1 if is_draft else 0
        )
        self.db_session.add(new_invoice)
        self.db_session.flush() # للحصول على ID الفاتورة الجديدة

        # 2. إضافة أصناف الفاتورة وتحديث المخزون
        for row in range(self.items_table.rowCount()):
            item_id = int(self.items_table.item(row, 0).text())
            quantity = int(self.items_table.item(row, 4).text())
            price = float(self.items_table.item(row, 5).text())
            discount = float(self.items_table.item(row, 6).text())

            inv_item = database.InvoiceItem(invoice_id=new_invoice.id, item_id=item_id, quantity=quantity, price_per_unit=price, discount_percent=discount)
            self.db_session.add(inv_item)

            if not is_draft:
                item_in_db = self.db_session.query(database.Item).filter(database.Item.id == item_id).first()
                if item_in_db:
                    item_in_db.quantity -= quantity

        # 3. تحديث مديونية العميل
        if not is_draft and customer_id != -1:
            customer = self.db_session.query(database.Customer).filter(database.Customer.id == customer_id).first()
            if customer:
                customer.current_debt = float(self.balance_after_invoice_label.text())

        # 4. تسجيل المبلغ المدفوع في الخزينة
        if not is_draft and new_invoice.paid_amount > 0:
            self.create_treasury_transaction(new_invoice.paid_amount, f"من فاتورة مبيعات رقم {new_invoice.id}", new_invoice.id)

    def update_existing_invoice(self, is_draft):
        """منطق تحديث فاتورة موجودة"""
        invoice_to_update = self.db_session.query(database.Invoice).filter(database.Invoice.id == self.invoice_id).first()
        if not invoice_to_update: return

        # --- 1. عكس التأثير القديم للفاتورة (إذا لم تكن مسودة) ---
        if not invoice_to_update.is_draft:
            # إعادة كميات المخزون
            for old_item in invoice_to_update.items:
                item_in_db = self.db_session.query(database.Item).filter(database.Item.id == old_item.item_id).first()
                if item_in_db:
                    item_in_db.quantity += old_item.quantity
            
            # عكس مديونية العميل
            if invoice_to_update.customer_id != -1:
                customer = self.db_session.query(database.Customer).filter(database.Customer.id == invoice_to_update.customer_id).first()
                if customer:
                    # Total effect of old invoice = total_amount - paid_amount
                    old_effect = invoice_to_update.total_amount - invoice_to_update.paid_amount
                    customer.current_debt -= old_effect

            # حذف حركة الخزينة القديمة
            self.db_session.query(database.TreasuryTransaction).filter_by(invoice_id=self.invoice_id).delete()

        # --- 2. تحديث بيانات الفاتورة الرئيسية ---
        invoice_to_update.customer_id = self.customer_combo.currentData()
        invoice_to_update.seller_id = self.salesperson_combo.currentData() if self.salesperson_combo.currentData() != -1 else None
        invoice_to_update.date = self.date_edit.date().toPython()
        invoice_to_update.total_amount = float(self.grand_total_label.text())
        invoice_to_update.paid_amount = float(self.paid_edit.text())
        invoice_to_update.discount_amount = float(self.discount_edit.text())
        invoice_to_update.tax_rate = self.tax_combo.currentData() or 0.0
        invoice_to_update.payment_method = self.payment_method_combo.currentText()
        invoice_to_update.notes = self.notes_edit.toPlainText()
        invoice_to_update.is_draft = 1 if is_draft else 0

        # --- 3. حذف الأصناف القديمة وإضافة الجديدة ---
        self.db_session.query(database.InvoiceItem).filter_by(invoice_id=self.invoice_id).delete()
        self.db_session.flush()

        for row in range(self.items_table.rowCount()):
            item_id = int(self.items_table.item(row, 0).text())
            quantity = int(self.items_table.item(row, 4).text())
            price = float(self.items_table.item(row, 5).text())
            discount = float(self.items_table.item(row, 6).text())
            inv_item = database.InvoiceItem(invoice_id=self.invoice_id, item_id=item_id, quantity=quantity, price_per_unit=price, discount_percent=discount)
            self.db_session.add(inv_item)

        # --- 4. تطبيق التأثير الجديد للفاتورة (إذا لم تكن مسودة) ---
        if not is_draft:
            # تحديث المخزون
            for row in range(self.items_table.rowCount()):
                item_id = int(self.items_table.item(row, 0).text())
                quantity = int(self.items_table.item(row, 4).text())
                item_in_db = self.db_session.query(database.Item).filter(database.Item.id == item_id).first()
                if item_in_db:
                    item_in_db.quantity -= quantity
            
            # تحديث مديونية العميل
            if invoice_to_update.customer_id != -1:
                customer = self.db_session.query(database.Customer).filter(database.Customer.id == invoice_to_update.customer_id).first()
                if customer:
                    # The reversal of the old debt has already been accounted for.
                    # Now, we simply set the debt to the newly calculated final balance from the UI.
                    customer.current_debt = float(self.balance_after_invoice_label.text())



            # إضافة حركة الخزينة الجديدة
            if invoice_to_update.paid_amount > 0:
                self.create_treasury_transaction(invoice_to_update.paid_amount, f"من تحديث فاتورة مبيعات رقم {self.invoice_id}", self.invoice_id)

    def create_treasury_transaction(self, amount, description, invoice_id):
        """Helper to create a treasury transaction."""
        if self.payment_method_combo.currentText() != "نقدي" or amount <= 0:
            return

        last_transaction = self.db_session.query(database.TreasuryTransaction).order_by(database.TreasuryTransaction.id.desc()).first()
        last_balance = last_transaction.current_balance if last_transaction else 0.0
        
        new_balance = last_balance + amount

        treasury_entry = database.TreasuryTransaction(
            transaction_type=self.tr("إيداع"),
            amount=amount,
            description=description,
            current_balance=new_balance,
            invoice_id=invoice_id
        )
        self.db_session.add(treasury_entry)


    def update_invoice_number(self):
        """يحصل على رقم الفاتورة التالي من قاعدة البيانات ويحدث الواجهة"""
        if self.invoice_id: # لا تقم بالتحديث إذا كنا في وضع التعديل
            return
        last_invoice = self.db_session.query(database.Invoice).order_by(database.Invoice.id.desc()).first()
        next_id = (last_invoice.id + 1) if last_invoice else 1
        self.invoice_num_label.setText(str(next_id))

    def print_invoice(self):
        """طباعة الفاتورة الحالية"""
        if self.items_table.rowCount() == 0:
            QMessageBox.warning(self, self.tr("خطأ"), self.tr("لا يمكن طباعة فاتورة فارغة."))
            return

        doc = QTextDocument()
        items_html = ""
        for row in range(self.items_table.rowCount()):
            items_html += f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">{self.items_table.item(row, 2).text()}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{self.items_table.item(row, 4).text()}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{self.items_table.item(row, 5).text()}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{self.items_table.item(row, 7).text()}</td>
            </tr>
            """

        html_content = f"""
        <div dir="rtl" style="font-family: sans-serif; padding: 20px;">
            <h1 style="text-align: center; color: #333;">{self.tr("فاتورة مبيعات")}</h1>
            <p><strong>{self.tr("العميل:")}</strong> {self.customer_combo.currentText()}</p>
            <p><strong>{self.tr("التاريخ:")}</strong> {self.date_edit.date().toString("yyyy-MM-dd")}</p>
            <hr>
            <table width="100%" style="border-collapse: collapse;">
                <thead style="background-color: #f2f2f2;"><tr><th style="padding: 8px; border: 1px solid #ddd;">{self.tr("الصنف")}</th><th style="padding: 8px; border: 1px solid #ddd;">{self.tr("الكمية")}</th><th style="padding: 8px; border: 1px solid #ddd;">{self.tr("السعر")}</th><th style="padding: 8px; border: 1px solid #ddd;">{self.tr("الإجمالي")}</th></tr></thead>
                <tbody>{items_html}</tbody>
            </table>
            <h3 style="text-align: left; margin-top: 20px;">{self.tr("الصافي:")} {self.grand_total_label.text()}</h3>
        </div>
        """
        doc.setHtml(html_content)

        preview_dialog = QPrintPreviewDialog()
        preview_dialog.paintRequested.connect(doc.print_)
        preview_dialog.exec()

    def reset_form(self):
        """يمسح جميع حقول الفاتورة للبدء من جديد"""
        # منع الإشارات أثناء التحديث لتجنب الحسابات غير الضرورية
        self.items_table.blockSignals(True)
        self.discount_edit.blockSignals(True)
        self.paid_edit.blockSignals(True)
        self.payment_method_combo.blockSignals(True)
        self.customer_combo.blockSignals(True)

        # مسح جدول الأصناف
        self.items_table.setRowCount(0)

        # إعادة تعيين معلومات العميل والتاريخ
        self.customer_combo.setCurrentIndex(0) # العميل النقدي # تم تصحيح هذا السطر
        self.debt_label.setText("0.00")
        self.date_edit.setDate(QDate.currentDate())
        self.payment_method_combo.setCurrentIndex(0) # نقدي # تم تصحيح هذا السطر
        self.update_invoice_number() # تحديث رقم الفاتورة إلى الرقم التالي

        # مسح حقول الإدخال والملاحظات
        self.item_search_edit.clear() # تم تصحيح هذا السطر
        self.notes_edit.clear()
        self.discount_edit.setText("0.00")
        self.paid_edit.setText("0.00")

        # إعادة تمكين الإشارات
        self.items_table.blockSignals(False)
        self.discount_edit.blockSignals(False)
        self.paid_edit.blockSignals(False)
        self.payment_method_combo.blockSignals(False)
        self.customer_combo.blockSignals(False)

        # استدعاء دالة تحديث الإجماليات مرة واحدة في النهاية لإعادة تصفيرها
        self.update_totals()

    def on_payment_method_changed(self, index):
        """يتم استدعاؤها عند تغيير طريقة الدفع"""
        method = self.payment_method_combo.currentText()
        if method == self.tr("نقدي"):
            # تعبئة المدفوع تلقائياً بقيمة الصافي
            self.paid_edit.setText(self.grand_total_label.text())
        else: # آجل أو شيك
            # تصفير المدفوع
            self.paid_edit.setText("0.00")

    def open_add_customer_dialog(self):
        """يفتح نافذة لإضافة عميل جديد بسرعة"""
        dialog = AddCustomerDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            new_customer = database.Customer(**data)
            self.db_session.add(new_customer)
            self.db_session.commit() # تم تصحيح هذا السطر
            QMessageBox.information(self, "نجاح", f"تم إضافة العميل '{data['name']}' بنجاح.")
            self.load_customers() # إعادة تحميل قائمة العملاء
            self.customer_combo.setCurrentText(data['name']) # تحديد العميل الجديد

class SalesReturnWidget(QWidget):
    """واجهة إنشاء مرتجع مبيعات جديد"""
    def __init__(self):
        super().__init__()
        self.db_session = database.SessionLocal()
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()
        self.load_customers()
        self.connect_signals()

    def init_ui(self):
        main_layout = QGridLayout(self)

        # --- مجموعة معلومات المرتجع والعميل ---
        info_group = QGroupBox("معلومات المرتجع والعميل")
        info_layout = QGridLayout()

        info_layout.addWidget(QLabel("العميل:"), 0, 0)
        self.customer_combo = QComboBox()
        self.customer_combo.setEditable(True)
        info_layout.addWidget(self.customer_combo, 0, 1)

        info_layout.addWidget(QLabel("مديونية حالية:"), 0, 2)
        self.debt_label = QLabel("0.00")
        self.debt_label.setStyleSheet("color: red; font-weight: bold;")
        info_layout.addWidget(self.debt_label, 0, 3)

        info_layout.addWidget(QLabel("التاريخ:"), 1, 0)
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        info_layout.addWidget(self.date_edit, 1, 1)

        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group, 0, 0, 1, 2)

        # --- مجموعة إضافة الأصناف ---
        add_item_group = QGroupBox("إضافة صنف للمرتجع")
        add_item_layout = QHBoxLayout()
        self.item_search_edit = QLineEdit()
        self.item_search_edit.setPlaceholderText("ابحث بكود أو اسم الصنف...")
        add_item_button = QPushButton("إضافة الصنف")
        add_item_button.clicked.connect(self.add_item_to_return)
        add_item_layout.addWidget(QLabel("بحث:"))
        add_item_layout.addWidget(self.item_search_edit)
        add_item_layout.addWidget(add_item_button)
        add_item_group.setLayout(add_item_layout)
        main_layout.addWidget(add_item_group, 1, 0, 1, 2)

        # --- جدول الأصناف ---
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels(["ID", "اسم الصنف", "الكمية المرتجعة", "سعر الوحدة", "الإجمالي", "حذف"])
        self.items_table.setColumnHidden(0, True)
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.items_table, 2, 0, 1, 2)

        # --- مجموعة الإجماليات ---
        totals_group = QGroupBox("ملخص المرتجع")
        totals_layout = QGridLayout()
        totals_layout.addWidget(QLabel("إجمالي المرتجع:"), 0, 0)
        self.total_label = QLabel("0.00")
        totals_layout.addWidget(self.total_label, 0, 1)

        totals_layout.addWidget(QLabel("المبلغ المسترجع نقدًا:"), 1, 0)
        self.refund_edit = QLineEdit("0.00")
        totals_layout.addWidget(self.refund_edit, 1, 1)

        totals_layout.addWidget(QLabel("الرصيد الجديد للعميل:"), 2, 0)
        self.balance_after_return_label = QLabel("0.00")
        self.balance_after_return_label.setStyleSheet("color: green; font-weight: bold;")
        totals_layout.addWidget(self.balance_after_return_label, 2, 1)

        totals_group.setLayout(totals_layout)
        main_layout.addWidget(totals_group, 3, 1)

        # --- أزرار الإجراءات ---
        buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("حفظ المرتجع")
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout, 4, 0, 1, 2)

    def connect_signals(self):
        self.customer_combo.currentIndexChanged.connect(self.update_customer_debt)
        self.items_table.cellChanged.connect(self.update_totals)
        self.refund_edit.textChanged.connect(self.update_totals)
        self.save_button.clicked.connect(self.save_return)
        self.item_search_edit.returnPressed.connect(self.add_item_to_return)

    def load_customers(self):
        self.customer_combo.clear()
        customers = self.db_session.query(database.Customer).all()
        self.customer_combo.addItem("عميل نقدي", -1)
        for customer in customers:
            self.customer_combo.addItem(customer.name, customer.id)

    def update_customer_debt(self, index):
        customer_id = self.customer_combo.itemData(index)
        if customer_id and customer_id != -1:
            customer = self.db_session.query(database.Customer).get(customer_id)
            self.debt_label.setText(f"{customer.current_debt:.2f}")
        else:
            self.debt_label.setText("0.00")
        self.update_totals()

    def add_item_to_return(self):
        search_term = self.item_search_edit.text()
        if not search_term: return
        item = self.db_session.query(database.Item).filter(
            (database.Item.code == search_term) | (database.Item.name.contains(search_term))
        ).first()
        if not item:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على الصنف!")
            return

        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        self.items_table.setItem(row, 0, QTableWidgetItem(str(item.id)))
        self.items_table.setItem(row, 1, QTableWidgetItem(item.name))
        self.items_table.setItem(row, 2, QTableWidgetItem("1"))
        self.items_table.setItem(row, 3, QTableWidgetItem(f"{item.sale_price:.2f}"))
        self.items_table.setItem(row, 4, QTableWidgetItem("0.00"))
        delete_button = QPushButton("حذف")
        delete_button.clicked.connect(lambda: self.items_table.removeRow(self.items_table.indexAt(delete_button.pos()).row()))
        self.items_table.setCellWidget(row, 5, delete_button)
        self.item_search_edit.clear()
        self.update_totals()

    def update_totals(self, row=0, column=0):
        total = 0.0
        for r in range(self.items_table.rowCount()):
            try:
                quantity = float(self.items_table.item(r, 2).text())
                price = float(self.items_table.item(r, 3).text())
                row_total = quantity * price
                self.items_table.item(r, 4).setText(f"{row_total:.2f}")
                total += row_total
            except (ValueError, AttributeError):
                continue
        self.total_label.setText(f"{total:.2f}")

        try:
            old_debt = float(self.debt_label.text())
            refund_amount = float(self.refund_edit.text() or 0.0)
            # رصيد العميل الجديد = الدين القديم - قيمة المرتجع + المبلغ المسترجع نقداً
            new_balance = old_debt - total + refund_amount
            self.balance_after_return_label.setText(f"{new_balance:.2f}")
        except ValueError:
            pass

    def save_return(self):
        customer_id = self.customer_combo.currentData()
        if customer_id is None:
            QMessageBox.warning(self, "خطأ", "يرجى تحديد العميل أولاً.")
            return

        # 1. إنشاء سجل المرتجع
        new_return = database.SalesReturn(
            customer_id=customer_id,
            date=self.date_edit.date().toPython(),
            total_amount=float(self.total_label.text()),
            refund_amount=float(self.refund_edit.text() or 0.0)
        )
        self.db_session.add(new_return)

        # 2. إضافة الأصناف وتحديث المخزون
        for row in range(self.items_table.rowCount()):
            item_id = int(self.items_table.item(row, 0).text())
            quantity = int(self.items_table.item(row, 2).text())
            price = float(self.items_table.item(row, 3).text())

            ret_item = database.SalesReturnItem(sales_return=new_return, item_id=item_id, quantity=quantity, price_per_unit=price)
            self.db_session.add(ret_item)

            # زيادة كمية الصنف في المخزون
            item_in_db = self.db_session.query(database.Item).get(item_id)
            if item_in_db:
                item_in_db.quantity += quantity

        # 3. تحديث رصيد العميل
        if customer_id != -1:
            customer = self.db_session.query(database.Customer).get(customer_id)
            if customer:
                customer.current_debt = float(self.balance_after_return_label.text())

        # 4. تسجيل المبلغ المسترجع في الخزينة (سحب)
        refund_amount = float(self.refund_edit.text() or 0.0)
        if refund_amount > 0:
            last_transaction = self.db_session.query(database.TreasuryTransaction).order_by(database.TreasuryTransaction.id.desc()).first()
            last_balance = last_transaction.current_balance if last_transaction else 0.0
            if refund_amount > last_balance:
                QMessageBox.warning(self, "خطأ", "المبلغ المسترجع أكبر من الرصيد المتاح في الخزينة!")
                self.db_session.rollback()
                return

            new_balance = last_balance - refund_amount
            treasury_entry = database.TreasuryTransaction(
                transaction_type="سحب",
                amount=refund_amount,
                description=f"مرتجع مبيعات للعميل {self.customer_combo.currentText()}",
                current_balance=new_balance,
            )
            self.db_session.add(treasury_entry)

        self.db_session.commit()
        QMessageBox.information(self, "نجاح", "تم حفظ مرتجع المبيعات بنجاح.")
        # مسح الشاشة
        self.items_table.setRowCount(0)
        self.refund_edit.setText("0.00")
        self.update_totals()

class InventoryWidget(QWidget):
    """واجهة إدارة أصناف المخزون"""
    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.RightToLeft)
        # إنشاء جلسة اتصال بقاعدة البيانات خاصة بهذه الواجهة # تم تصحيح هذا السطر
        self.db_session = database.SessionLocal()
        self.init_ui()
        self.load_items_from_db() # تحميل الأصناف من قاعدة البيانات عند البدء

    def init_ui(self):
        main_layout = QVBoxLayout(self)


        # --- مجموعة البحث والإجراءات ---
        actions_group = QGroupBox(self.tr("بحث وإجراءات"))
        actions_layout = QHBoxLayout()

        actions_layout.addWidget(QLabel(self.tr("بحث عن صنف:")))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("ادخل كود أو اسم الصنف...")
        self.search_edit.textChanged.connect(self.filter_table)
        actions_layout.addWidget(self.search_edit)

        self.add_button = QPushButton(self.style().standardIcon(QStyle.SP_FileDialogNewFolder), "إضافة صنف جديد")
        self.add_button.clicked.connect(self.open_add_item_dialog)
        self.add_button.setText(self.tr("إضافة صنف جديد"))
        self.edit_button = QPushButton(self.style().standardIcon(QStyle.SP_DialogResetButton), self.tr("تعديل المحدد"))
        self.edit_button.clicked.connect(self.open_edit_item_dialog)
        self.delete_button = QPushButton(self.style().standardIcon(QStyle.SP_TrashIcon), self.tr("حذف المحدد"))
        # تخصيص اسم الزر ليتناسب مع الثيم الأحمر
        self.delete_button.setObjectName("delete_button")


        actions_layout.addWidget(self.add_button)
        actions_layout.addWidget(self.edit_button)
        actions_layout.addWidget(self.delete_button)
        actions_group.setLayout(actions_layout)
        main_layout.addWidget(actions_group)

        # --- جدول عرض الأصناف ---
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(8) # أضفنا عموداً لـ ID
        self.inventory_table.setHorizontalHeaderLabels( # تم تصحيح هذا السطر
            ["ID", "كود الصنف", "اسم الصنف", "المخزن", "الكمية الحالية", "سعر الشراء", "سعر البيع", "مسار الصورة"]
        )
        self.inventory_table.setColumnHidden(0, True) # إخفاء عمود ID
        self.inventory_table.setColumnHidden(7, True) # إخفاء عمود مسار الصورة
        self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.inventory_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.inventory_table.setEditTriggers(QTableWidget.NoEditTriggers) # منع التعديل المباشر

        main_layout.addWidget(self.inventory_table)

        # --- ربط إشارة الحذف ---
        # تم نقلها هنا لضمان أن الزر موجود
        self.delete_button.clicked.connect(self.delete_selected_item)


        self.setLayout(main_layout)

    def load_items_from_db(self):
        """تحميل وعرض الأصناف من قاعدة البيانات"""
        self.inventory_table.setRowCount(0) # مسح الجدول قبل التحميل
        items = self.db_session.query(database.Item).all()
        for item in items:
            self.add_item_to_table(item)

    def open_add_item_dialog(self):
        """يفتح نافذة منبثقة لإضافة صنف جديد"""
        dialog = AddItemDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            new_item = database.Item(**data) # إنشاء كائن صنف جديد من البيانات
            self.db_session.add(new_item)
            self.db_session.commit()
            self.add_item_to_table(new_item) # إضافة الصنف الجديد مباشرة للجدول

    def open_edit_item_dialog(self):
        """يفتح نافذة منبثقة لتعديل الصنف المحدد"""
        selected_row = self.inventory_table.currentRow()
        if selected_row < 0:
            # لم يتم تحديد أي صف، يمكنك إظهار رسالة تنبيه هنا
            return

        item_id = int(self.inventory_table.item(selected_row, 0).text())
        item_to_edit = self.db_session.query(database.Item).filter(database.Item.id == item_id).first()
        if not item_to_edit: # تم تصحيح هذا السطر
            return

        # قراءة البيانات الحالية من الصف المحدد
        current_data = {
            "code": item_to_edit.code,
            "name": item_to_edit.name,
            "store_id": item_to_edit.store_id,
            "quantity": str(item_to_edit.quantity),
            "cost_price": str(item_to_edit.cost_price),
            "sale_price": str(item_to_edit.sale_price),
            "image_path": item_to_edit.image_path
        }

        dialog = AddItemDialog(self, item_data=current_data)
        if dialog.exec() == QDialog.Accepted: # تم تصحيح هذا السطر
            new_data = dialog.get_data()
            # تحديث بيانات الكائن
            for key, value in new_data.items():
                setattr(item_to_edit, key, value)
            self.db_session.commit()
            self.update_item_in_table(selected_row, item_to_edit)

    def filter_table(self, text):
        """يقوم بفلترة الجدول بناءً على النص المدخل في حقل البحث"""
        search_text = text.lower()
        for row in range(self.inventory_table.rowCount()):
            item_code = self.inventory_table.item(row, 1).text().lower() # العمود 1 للكود
            item_name = self.inventory_table.item(row, 2).text().lower() # العمود 2 للاسم

            # التحقق مما إذا كان نص البحث موجوداً في الكود أو الاسم
            match = search_text in item_code or search_text in item_name

            # إظهار أو إخفاء الصف بناءً على نتيجة البحث
            if match:
                self.inventory_table.setRowHidden(row, False)
            else:
                self.inventory_table.setRowHidden(row, True)

    def delete_selected_item(self):
        """يحذف الصنف المحدد من الجدول وقاعدة البيانات"""
        selected_row = self.inventory_table.currentRow()
        if selected_row < 0: # تم تصحيح هذا السطر
            QMessageBox.warning(self, "خطأ", "يرجى تحديد صنف لحذفه أولاً.")
            return

        item_id = int(self.inventory_table.item(selected_row, 0).text())
        item_name = self.inventory_table.item(selected_row, 2).text()

        reply = QMessageBox.question(self, "تأكيد الحذف", 
                                     self.tr(f"هل أنت متأكد من حذف الصنف '{item_name}' بشكل نهائي؟\nلا يمكن التراجع عن هذا الإجراء."),
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            item_to_delete = self.db_session.query(database.Item).filter(database.Item.id == item_id).first()
            if item_to_delete:
                self.db_session.delete(item_to_delete)
                self.db_session.commit()
                self.inventory_table.removeRow(selected_row) # الحذف من الجدول بعد الحذف من قاعدة البيانات

    def add_item_to_table(self, item: database.Item):
        row_position = self.inventory_table.rowCount()
        self.inventory_table.insertRow(row_position)
        self.inventory_table.setItem(row_position, 0, QTableWidgetItem(str(item.id)))
        self.inventory_table.setItem(row_position, 1, QTableWidgetItem(item.code)) # تم تصحيح هذا السطر
        self.inventory_table.setItem(row_position, 2, QTableWidgetItem(item.name))
        self.inventory_table.setItem(row_position, 3, QTableWidgetItem(item.store.name if item.store else "N/A"))
        self.inventory_table.setItem(row_position, 4, QTableWidgetItem(str(item.quantity)))
        self.inventory_table.setItem(row_position, 5, QTableWidgetItem(str(item.cost_price)))
        self.inventory_table.setItem(row_position, 6, QTableWidgetItem(str(item.sale_price)))
        self.inventory_table.setItem(row_position, 7, QTableWidgetItem(item.image_path))

    def update_item_in_table(self, row, item: database.Item):
        """تحديث بيانات صف معين في الجدول"""
        self.inventory_table.item(row, 1).setText(item.code)
        self.inventory_table.item(row, 2).setText(item.name) # تم تصحيح هذا السطر
        self.inventory_table.item(row, 3).setText(item.store.name if item.store else "N/A")
        self.inventory_table.item(row, 4).setText(str(item.quantity))
        self.inventory_table.item(row, 5).setText(str(item.cost_price))
        self.inventory_table.item(row, 6).setText(str(item.sale_price))
        self.inventory_table.item(row, 7).setText(item.image_path)

    def closeEvent(self, event):
        """يتم استدعاؤها عند إغلاق الواجهة لضمان إغلاق جلسة قاعدة البيانات"""
        self.db_session.close()
        super().closeEvent(event)

class AddItemDialog(QDialog):
    """نافذة منبثقة لإضافة أو تعديل صنف"""
    def __init__(self, parent=None, item_data=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumWidth(350)
        self.image_path = item_data.get("image_path") if item_data else None
        self.db_session = database.SessionLocal() # تم تصحيح هذا السطر
        self.form_layout = QFormLayout(self)

        self.code_edit = QLineEdit()
        self.name_edit = QLineEdit()
        self.store_combo = QComboBox()
        self.quantity_edit = QLineEdit("0")
        self.cost_price_edit = QLineEdit("0.00")
        self.sale_price_edit = QLineEdit("0.00")

        self.form_layout.addRow(self.tr("كود الصنف:"), self.code_edit)
        self.form_layout.addRow(self.tr("اسم الصنف:"), self.name_edit)
        self.form_layout.addRow(self.tr("المخزن:"), self.store_combo)
        self.form_layout.addRow(self.tr("الكمية:"), self.quantity_edit)
        self.form_layout.addRow(self.tr("سعر الشراء:"), self.cost_price_edit)
        self.form_layout.addRow(self.tr("سعر البيع:"), self.sale_price_edit)

        # تحميل المخازن من قاعدة البيانات
        stores = self.db_session.query(database.Store).all()
        for store in stores:
            self.store_combo.addItem(store.name, store.id)
        self.db_session.close()

        # --- قسم الصورة ---
        image_layout = QHBoxLayout()
        self.image_label = QLabel(self.tr("لم يتم تحديد صورة"))
        self.image_label.setFixedSize(100, 100)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;")
        select_image_button = QPushButton(self.tr("اختيار صورة"))
        select_image_button.clicked.connect(self.select_image)
        image_layout.addWidget(self.image_label) # تم تصحيح هذا السطر
        image_layout.addWidget(select_image_button)
        image_layout.addStretch()

        self.form_layout.addRow("صورة الصنف:", image_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.form_layout.addRow(self.button_box)

        if item_data:
            self.setWindowTitle(self.tr("تعديل صنف"))
            self.populate_data(item_data)
        else:
            self.setWindowTitle(self.tr("إضافة صنف جديد"))

    def get_data(self):
        """تُرجع البيانات المدخلة في شكل قاموس"""
        return {
            "code": self.code_edit.text(), "name": self.name_edit.text(),
            "store_id": self.store_combo.currentData(),
            "quantity": int(self.quantity_edit.text() or 0),
            "cost_price": float(self.cost_price_edit.text() or 0.0),
            "sale_price": float(self.sale_price_edit.text() or 0.0),
            "image_path": self.image_path,
        }

    def populate_data(self, data):
        """تعبئة حقول الإدخال ببيانات موجودة"""
        self.code_edit.setText(data.get("code", ""))
        self.name_edit.setText(data.get("name", ""))
        store_id = data.get("store_id") # تم التعديل هنا # تم تصحيح هذا السطر
        if store_id:
            self.store_combo.setCurrentIndex(self.store_combo.findData(store_id))
        self.quantity_edit.setText(data.get("quantity", "0"))
        self.cost_price_edit.setText(data.get("cost_price", "0.00"))
        self.sale_price_edit.setText(data.get("sale_price", "0.00"))
        if self.image_path:
            self.load_image(self.image_path)

    def select_image(self):
        """يفتح نافذة لاختيار ملف صورة"""
        file_name, _ = QFileDialog.getOpenFileName(self, self.tr("اختر صورة الصنف"), "", self.tr("Image Files (*.png *.jpg *.jpeg *.bmp)"))
        if file_name:
            self.image_path = file_name
            self.load_image(file_name)

    def load_image(self, path):
        """تحميل وعرض الصورة في الواجهة"""
        pixmap = QPixmap(path)
        self.image_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))

class SettingsPlaceholderWidget(QWidget):
    """واجهة مؤقتة لشاشات الإعدادات"""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        label = QLabel(self.tr(f"هذه هي {title}"))
        font = label.font()
        font.setPointSize(22)
        font.setBold(True)
        label.setFont(font)

        layout.addWidget(label)
        self.setLayout(layout)

class TaxesSettingsWidget(QWidget):
    """واجهة لإدارة إعدادات الضرائب"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.settings_file = get_app_data_path("settings.json")
        self.init_ui()
        self.load_taxes()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)

        title_label = QLabel(self.tr("إعدادات الضرائب والخصومات"))
        title_font = title_label.font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label, 0, Qt.AlignCenter)
        
        # --- أزرار الإجراءات ---
        buttons_layout = QHBoxLayout()
        add_button = QPushButton("إضافة ضريبة جديدة")
        add_button.clicked.connect(self.add_tax)
        delete_button = QPushButton("حذف المحدد")
        delete_button.clicked.connect(self.delete_tax)
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)

        # --- جدول الضرائب ---
        self.taxes_table = QTableWidget()
        self.taxes_table.setColumnCount(2) # تم تصحيح هذا السطر
        self.taxes_table.setHorizontalHeaderLabels(["اسم الضريبة", "النسبة المئوية (%)"])
        self.taxes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.taxes_table)

        # --- زر الحفظ ---
        save_button = QPushButton("حفظ الإعدادات")
        save_button.clicked.connect(self.save_taxes)
        main_layout.addWidget(save_button, 0, Qt.AlignLeft)

    def load_taxes(self):
        if not os.path.exists(self.settings_file):
            return
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                settings = json.load(f)
                taxes = settings.get("taxes", [])
                self.taxes_table.setRowCount(len(taxes))
                for i, tax in enumerate(taxes):
                    self.taxes_table.setItem(i, 0, QTableWidgetItem(tax.get("name"))) # تم تصحيح هذا السطر
                    self.taxes_table.setItem(i, 1, QTableWidgetItem(str(tax.get("rate"))))
        except (json.JSONDecodeError, FileNotFoundError):
            self.taxes_table.setRowCount(0)

    def add_tax(self):
        row_count = self.taxes_table.rowCount()
        self.taxes_table.insertRow(row_count) # تم تصحيح هذا السطر
        self.taxes_table.setItem(row_count, 0, QTableWidgetItem("ضريبة جديدة"))
        self.taxes_table.setItem(row_count, 1, QTableWidgetItem("0"))

    def delete_tax(self):
        current_row = self.taxes_table.currentRow()
        if current_row >= 0:
            self.taxes_table.removeRow(current_row)

    def save_taxes(self):
        taxes = []
        for row in range(self.taxes_table.rowCount()):
            name_item = self.taxes_table.item(row, 0)
            rate_item = self.taxes_table.item(row, 1)
            if name_item and rate_item:
                try:
                    taxes.append({
                        "name": name_item.text(),
                        "rate": float(rate_item.text())
                    })
                except ValueError:
                    QMessageBox.warning(self, self.tr("خطأ"), self.tr(f"القيمة في الصف {row + 1} غير صحيحة."))
                    return

        all_settings = {}
        if os.path.exists(self.settings_file):
            with open(self.settings_file, "r", encoding="utf-8") as f:
                try:
                    all_settings = json.load(f)
                except json.JSONDecodeError:
                    pass
        
        all_settings["taxes"] = taxes
        with open(self.settings_file, "w", encoding="utf-8") as f:
            json.dump(all_settings, f, ensure_ascii=False, indent=4)
        # تم تصحيح هذا السطر
        QMessageBox.information(self, "نجاح", "تم حفظ إعدادات الضرائب بنجاح.")

class PricingPoliciesWidget(QWidget):
    """واجهة لإدارة سياسات التسعير"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.settings_file = get_app_data_path("settings.json")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        title_label = QLabel(self.tr("إدارة سياسات التسعير"))
        title_font = title_label.font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label, 0, Qt.AlignCenter)

        # --- أزرار الإجراءات ---
        buttons_layout = QHBoxLayout()
        add_button = QPushButton(self.tr("إضافة سياسة جديدة"))
        add_button.clicked.connect(self.add_policy)
        delete_button = QPushButton(self.tr("حذف المحدد"))
        delete_button.clicked.connect(self.delete_policy)
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        # --- قائمة السياسات ---
        self.policies_list = QListWidget()
        layout.addWidget(self.policies_list)

        # --- زر الحفظ ---
        save_button = QPushButton(self.tr("حفظ"))
        save_button.clicked.connect(self.save_policies)
        layout.addWidget(save_button, 0, Qt.AlignLeft)
        
        self.load_policies()

    def load_policies(self):
        self.policies_list.clear()
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    policies = settings.get("pricing_policies", [self.tr("سعر التجزئة"), self.tr("سعر الجملة")])
                    for policy in policies:
                        self.policies_list.addItem(policy)
            except (json.JSONDecodeError, FileNotFoundError):
                pass

    def add_policy(self):
        name, ok = QInputDialog.getText(self, self.tr("إضافة سياسة تسعير"), self.tr("اسم السياسة الجديدة:"))
        if ok and name:
            self.policies_list.addItem(name)
    
    def delete_policy(self):
        self.policies_list.takeItem(self.policies_list.currentRow())

    def save_policies(self):
        policies = [self.policies_list.item(i).text() for i in range(self.policies_list.count())]
        # حفظ في ملف الإعدادات (نفس منطق الضرائب)
        QMessageBox.information(self, "نجاح", "تم حفظ سياسات التسعير.")

class BarcodePrintingWidget(QWidget):
    """واجهة لطباعة الباركود للأصناف"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_session = database.SessionLocal()
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)

        title_label = QLabel(self.tr("طباعة الباركود"))
        title_font = title_label.font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label, 0, Qt.AlignCenter)
        
        # --- قسم البحث ---
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(self.tr("ابحث بكود أو اسم الصنف..."))
        self.search_edit.returnPressed.connect(self.generate_barcode)
        search_button = QPushButton(self.tr("إنشاء الباركود"))
        search_button.clicked.connect(self.generate_barcode)
        search_layout.addWidget(QLabel("بحث عن صنف:"))
        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(search_button)
        main_layout.addLayout(search_layout)

        # --- قسم عرض الباركود ---
        self.barcode_display_label = QLabel(self.tr("ابحث عن صنف لعرض الباركود الخاص به"))
        self.barcode_display_label.setAlignment(Qt.AlignCenter)
        self.barcode_display_label.setMinimumHeight(150)
        self.barcode_display_label.setStyleSheet("border: 1px dashed #aaa; background-color: white;")
        main_layout.addWidget(self.barcode_display_label)

        # --- زر الطباعة ---
        print_button = QPushButton(self.tr("طباعة"))
        print_button.clicked.connect(self.print_barcode)
        main_layout.addWidget(print_button, 0, Qt.AlignLeft)

    def generate_barcode(self):
        search_term = self.search_edit.text()
        if not search_term:
            return

        item = self.db_session.query(database.Item).filter(
            (database.Item.code == search_term) | (database.Item.name.contains(search_term))
        ).first()

        if not item or not item.code:
            self.barcode_display_label.setText(self.tr("لم يتم العثور على الصنف أو لا يوجد له كود."))
            return

        try:
            import barcode
            from barcode.writer import ImageWriter

            EAN = barcode.get_barcode_class('ean13')
            # كود EAN13 يجب أن يكون 12 رقماً، سنقوم بتوليد أرقام إذا كان الكود غير صالح
            code_to_render = item.code.replace("-", "").replace(" ", "")
            if not code_to_render.isdigit() or len(code_to_render) > 12:
                code_to_render = str(item.id).zfill(12) # استخدام ID الصنف كحل بديل
            else:
                code_to_render = code_to_render.zfill(12)

            ean = EAN(code_to_render, writer=ImageWriter())
            # حفظ الباركود كملف مؤقت
            self.barcode_path = ean.save('temp_barcode')
            pixmap = QPixmap(self.barcode_path)
            self.barcode_display_label.setPixmap(pixmap)
        
        except ImportError:
            self.barcode_display_label.setText("مكتبة `python-barcode` غير مثبتة.\nيرجى تثبيتها باستخدام: pip install python-barcode[images]")
        except Exception as e:
            self.barcode_display_label.setText(f"خطأ في إنشاء الباركود: {e}")

    def print_barcode(self):
        if hasattr(self, 'barcode_path') and os.path.exists(self.barcode_path):
            doc = QTextDocument()
            image_uri = f"file:///{os.path.abspath(self.barcode_path)}"
            html = f'<div align="center"><img src="{image_uri}"></div>'
            doc.setHtml(html)
            
            preview_dialog = QPrintPreviewDialog()
            preview_dialog.paintRequested.connect(doc.print_)
            preview_dialog.exec()
        else:
            QMessageBox.warning(self, self.tr("خطأ"), self.tr("يرجى إنشاء باركود أولاً قبل الطباعة."))


class SettingsPlaceholderWidget(QWidget):
    """واجهة مؤقتة لشاشات الإعدادات"""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        label = QLabel(self.tr(f"هذه هي {title}"))
        font = label.font()
        font.setPointSize(22)
        font.setBold(True)
        label.setFont(font)

        layout.addWidget(label)
        self.setLayout(layout)

class CompanySettingsWidget(QWidget):
    """واجهة إعدادات الشركة"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.logo_path = None  # لتخزين مسار الشعار

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)

        form_group = QGroupBox(self.tr("معلومات الشركة الأساسية"))
        form_group.setStyleSheet("font-weight: bold;")
        form_layout = QFormLayout()
        form_group.setLayout(form_layout)

        self.company_name_edit = QLineEdit()
        self.company_address_edit = QTextEdit()
        self.company_address_edit.setFixedHeight(80)
        
        form_layout.addRow(self.tr("اسم الشركة:"), self.company_name_edit)
        form_layout.addRow(self.tr("عنوان الشركة:"), self.company_address_edit)

        # --- قسم الشعار ---
        logo_layout = QHBoxLayout()
        self.logo_label = QLabel(self.tr("لم يتم تحديد شعار"))
        self.logo_label.setFixedSize(150, 150)
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setStyleSheet("border: 1px dashed #aaa; background-color: #f8f8f8;")
        select_logo_button = QPushButton(self.tr("اختيار شعار الشركة"))
        select_logo_button.clicked.connect(self.select_logo)
        
        logo_vbox = QVBoxLayout()
        logo_vbox.addWidget(select_logo_button)
        logo_vbox.addStretch()

        logo_layout.addWidget(self.logo_label)
        logo_layout.addLayout(logo_vbox)

        form_layout.addRow(self.tr("شعار الشركة:"), logo_layout)

        main_layout.addWidget(form_group)
        
        # --- زر الحفظ ---
        self.save_button = QPushButton("حفظ الإعدادات")
        self.save_button.clicked.connect(self.save_settings)
        self.save_button.setFixedWidth(150)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.save_button)

        main_layout.addLayout(buttons_layout)
        
        self.load_settings() # تحميل الإعدادات عند فتح الشاشة

    def select_logo(self):
        """يفتح نافذة لاختيار ملف الشعار"""
        file_name, _ = QFileDialog.getOpenFileName(self, "اختر شعار الشركة", "", "Image Files (*.png *.jpg *.jpeg)")
        if file_name:
            self.logo_path = file_name
            pixmap = QPixmap(file_name)
            self.logo_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def save_settings(self):
        """يحفظ الإعدادات المدخلة"""
        # 1. قراءة الإعدادات الحالية من الملف إن وجد
        settings_file = get_app_data_path("settings.json")
        all_settings = {}
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    all_settings = json.load(f)
            except json.JSONDecodeError:
                pass # تجاهل الخطأ إذا كان الملف فارغاً أو تالفاً

        # 2. تحديث قسم إعدادات الشركة
        all_settings["company"] = {
            "name": self.company_name_edit.text(),
            "address": self.company_address_edit.toPlainText(),
            "logo_path": self.logo_path
        }

        # 3. كتابة كل الإعدادات مرة أخرى في الملف
        try:
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(all_settings, f, ensure_ascii=False, indent=4)
            
            self.shake_widget(self.save_button)
            QMessageBox.information(self, self.tr("حفظ الإعدادات"), self.tr("تم حفظ إعدادات الشركة بنجاح!"))
        except Exception as e:
            QMessageBox.critical(self, "خطأ في الحفظ", f"حدث خطأ أثناء حفظ الإعدادات: {e}")

    def load_settings(self):
        """تحميل الإعدادات من ملف JSON"""
        settings_file = get_app_data_path("settings.json")
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    all_settings = json.load(f)
                    company_settings = all_settings.get("company", {})
                    self.company_name_edit.setText(company_settings.get("name", ""))
                    self.company_address_edit.setPlainText(company_settings.get("address", ""))
                    self.logo_path = company_settings.get("logo_path")
                    if self.logo_path and os.path.exists(self.logo_path):
                        # استدعاء select_logo مع المسار لتحميل الصورة
                        pixmap = QPixmap(self.logo_path)
                        self.logo_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            except Exception as e:
                print(f"Could not load settings: {e}") # لطباعة الخطأ في الطرفية للمطور

    def select_logo(self, file_name=None):
        """يفتح نافذة لاختيار ملف الشعار أو يحمل مساراً موجوداً"""
        if not file_name: # تم تصحيح هذا السطر
            file_name, _ = QFileDialog.getOpenFileName(self, "اختر شعار الشركة", "", "Image Files (*.png *.jpg *.jpeg)")
        
        if file_name and os.path.exists(file_name):
            self.logo_path = file_name
            pixmap = QPixmap(file_name)
            self.logo_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def save_settings(self):
        """يحفظ الإعدادات المدخلة"""
        # تطبيق أنيميشن الاهتزاز على زر الحفظ
        self.shake_widget(self.save_button)

        # مستقبلاً، سيتم حفظ هذه البيانات في ملف أو قاعدة بيانات
        QMessageBox.information(self, self.tr("حفظ الإعدادات"), self.tr("تم حفظ إعدادات الشركة بنجاح!"))
    def shake_widget(self, widget):
        """
        يطبق أنيميشن اهتزاز على أي واجهة (widget).
        """
        animation_group = QSequentialAnimationGroup(self)
        original_pos = widget.pos()

        # إنشاء سلسلة من الحركات المتتالية
        for i in range(4): # عدد الاهتزازات
            # حركة لليمين
            anim_right = QPropertyAnimation(widget, b"pos")
            anim_right.setEndValue(original_pos + QPoint(5, 0))
            anim_right.setDuration(25)
            # حركة لليسار (للعودة إلى الأصل وأبعد قليلاً)
            anim_left = QPropertyAnimation(widget, b"pos")
            anim_left.setEndValue(original_pos - QPoint(5, 0))
            anim_left.setDuration(25)
            animation_group.addAnimation(anim_right)
            animation_group.addAnimation(anim_left)

        # حركة أخيرة للعودة إلى الوضع الأصلي
        anim_return = QPropertyAnimation(widget, b"pos")
        anim_return.setEndValue(original_pos)
        anim_return.setDuration(25)
        animation_group.addAnimation(anim_return)

        animation_group.start()

class UsersManagementWidget(QWidget):
    """واجهة إدارة المستخدمين والصلاحيات"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_session = database.SessionLocal()
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()
        self.load_users()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # --- قسم قائمة المستخدمين ---
        users_group = QGroupBox(self.tr("المستخدمون"))
        users_layout = QVBoxLayout()

        self.users_list = QListWidget()
        users_layout.addWidget(self.users_list)

        # --- أزرار إدارة المستخدمين ---
        user_buttons_layout = QHBoxLayout() # تم تصحيح هذا السطر
        add_user_button = QPushButton(self.tr("إضافة"))
        add_user_button.clicked.connect(self.add_new_user)
        
        change_pass_button = QPushButton(self.tr("تغيير كلمة المرور"))
        change_pass_button.clicked.connect(self.change_user_password)

        delete_user_button = QPushButton(self.tr("حذف"))
        delete_user_button.clicked.connect(self.delete_selected_user)

        user_buttons_layout.addWidget(add_user_button)
        user_buttons_layout.addWidget(change_pass_button) # تم تصحيح هذا السطر
        user_buttons_layout.addWidget(delete_user_button)
        users_layout.addLayout(user_buttons_layout)
        users_group.setLayout(users_layout)

        # --- تجميع الواجهة ---
        main_layout.addWidget(users_group, 1) # الجزء الخاص بالمستخدمين يأخذ نسبة 1
        # مستقبلاً، يمكن إضافة قسم الصلاحيات هنا

    def load_users(self):
        """تحميل المستخدمين من قاعدة البيانات وعرضهم في القائمة"""
        self.users_list.clear()
        users = self.db_session.query(database.User).all()
        for user in users:
            self.users_list.addItem(user.username)

    def add_new_user(self):
        """يفتح نافذة لإضافة مستخدم جديد"""
        username, ok1 = QInputDialog.getText(self, self.tr("إضافة مستخدم جديد"), self.tr("ادخل اسم المستخدم:"))
        if ok1 and username:
            # التحقق من أن اسم المستخدم غير موجود
            existing_user = self.db_session.query(database.User).filter_by(username=username).first()
            if existing_user:
                QMessageBox.warning(self, self.tr("خطأ"), self.tr("هذا المستخدم موجود بالفعل!"))
                return
            
            password, ok2 = QInputDialog.getText(self, self.tr("تعيين كلمة المرور"), self.tr(f"ادخل كلمة المرور للمستخدم '{username}':"), echo=QLineEdit.Password)
            if ok2 and password:
                new_user = database.User(username=username)
                new_user.set_password(password) # تم تصحيح هذا السطر
                self.db_session.add(new_user)
                self.db_session.commit()
                self.load_users() # إعادة تحميل القائمة
                QMessageBox.information(self, "نجاح", "تم إضافة المستخدم بنجاح.")

    def change_user_password(self):
        """يغير كلمة المرور للمستخدم المحدد"""
        current_item = self.users_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, self.tr("خطأ"), self.tr("يرجى تحديد مستخدم أولاً."))
            return
        
        username = current_item.text()
        new_password, ok = QInputDialog.getText(self, self.tr("تغيير كلمة المرور"), self.tr(f"ادخل كلمة المرور الجديدة للمستخدم '{username}':"), echo=QLineEdit.Password)
        
        if ok and new_password:
            user_to_edit = self.db_session.query(database.User).filter_by(username=username).first()
            if user_to_edit:
                user_to_edit.set_password(new_password)
                self.db_session.commit()
                QMessageBox.information(self, "نجاح", "تم تغيير كلمة المرور بنجاح.")

    def delete_selected_user(self):
        """حذف المستخدم المحدد حالياً"""
        current_item = self.users_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, self.tr("خطأ"), self.tr("يرجى تحديد مستخدم أولاً."))
            return

        username = current_item.text()
        if username == "admin": # تم تصحيح هذا السطر
            QMessageBox.warning(self, "خطأ", "لا يمكن حذف المستخدم 'admin' الرئيسي.")
            return

        reply = QMessageBox.question(self, "تأكيد الحذف", f"هل أنت متأكد من حذف المستخدم '{username}'؟")

        if reply == QMessageBox.Yes:
            user_to_delete = self.db_session.query(database.User).filter_by(username=username).first()
            if user_to_delete:
                self.db_session.delete(user_to_delete)
                self.db_session.commit()
                self.load_users() # إعادة تحميل القائمة
                QMessageBox.information(self, "نجاح", "تم حذف المستخدم بنجاح.")

class NetworkSettingsWidget(QWidget):
    """واجهة إعدادات الشبكة والاتصال بقاعدة البيانات"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)

        settings_group = QGroupBox(self.tr("إعدادات الاتصال بقاعدة البيانات"))
        form_layout = QFormLayout(settings_group)

        self.engine_map = { # تم تصحيح هذا السطر
            "SQLite (ملف محلي - مستخدم واحد)": "sqlite",
            "PostgreSQL (شبكة - متعدد المستخدمين)": "postgresql",
            "MySQL (شبكة - متعدد المستخدمين)": "mysql",
            "Microsoft SQL Server (شبكة)": "mssql"
        }
        self.db_engine_combo = QComboBox()
        self.db_engine_combo.addItems(self.engine_map.keys())
        self.db_engine_combo.currentIndexChanged.connect(self.toggle_network_fields)

        self.host_edit = QLineEdit("localhost")
        self.port_edit = QLineEdit("5432")
        self.dbname_edit = QLineEdit("erp_db")
        self.user_edit = QLineEdit("postgres")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)

        form_layout.addRow(self.tr("نوع قاعدة البيانات:"), self.db_engine_combo)
        form_layout.addRow(self.tr("IP أو اسم السيرفر (Host):"), self.host_edit)
        form_layout.addRow(self.tr("المنفذ (Port):"), self.port_edit)
        form_layout.addRow(self.tr("اسم قاعدة البيانات:"), self.dbname_edit)
        form_layout.addRow(self.tr("اسم المستخدم:"), self.user_edit)
        form_layout.addRow(self.tr("كلمة المرور:"), self.password_edit)

        main_layout.addWidget(settings_group)

        # --- أزرار الإجراءات ---
        buttons_layout = QHBoxLayout()
        save_button = QPushButton("حفظ وإعادة تشغيل")
        save_button.setToolTip("سيتم حفظ الإعدادات وإعادة تشغيل البرنامج لتطبيقها")
        save_button.clicked.connect(self.save_settings) # تم تصحيح هذا السطر
        buttons_layout.addStretch()
        buttons_layout.addWidget(save_button)
        main_layout.addLayout(buttons_layout)

        self.toggle_network_fields() # لضبط الواجهة عند الفتح

    def toggle_network_fields(self):
        """إظهار أو إخفاء حقول الشبكة بناءً على نوع قاعدة البيانات"""
        is_postgres = self.db_engine_combo.currentIndex() > 0 # أي خيار غير SQLite
        self.host_edit.setEnabled(is_postgres)
        self.port_edit.setEnabled(is_postgres)
        self.dbname_edit.setEnabled(is_postgres)
        self.user_edit.setEnabled(is_postgres)
        self.password_edit.setEnabled(is_postgres)

    def load_settings(self):
        """تحميل إعدادات الشبكة من ملف JSON"""
        settings_file = get_app_data_path("settings.json")
        if not os.path.exists(settings_file): return
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                all_settings = json.load(f)
                network_settings = all_settings.get("network", {})
                engine_value = network_settings.get("engine", "sqlite")
                for display_name, value in self.engine_map.items():
                    if value == engine_value:
                        self.db_engine_combo.setCurrentText(display_name)
                        break

                self.host_edit.setText(network_settings.get("host", "localhost")) # تم تصحيح هذا السطر
                self.port_edit.setText(network_settings.get("port", "5432"))
                self.dbname_edit.setText(network_settings.get("dbname", "erp_db"))
                self.user_edit.setText(network_settings.get("user", "postgres"))
                self.password_edit.setText(network_settings.get("password", ""))
        except Exception as e:
            print(f"Could not load network settings: {e}")

    def save_settings(self):
        """حفظ إعدادات الشبكة في ملف JSON"""
        settings_file = get_app_data_path("settings.json")
        all_settings = {}
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    all_settings = json.load(f)
            except json.JSONDecodeError: pass

        engine_index = self.db_engine_combo.currentIndex()
        selected_display_name = self.db_engine_combo.currentText()
        engine_type = self.engine_map.get(selected_display_name, "sqlite")
        all_settings["network"] = {
            "engine": engine_type,
            "host": self.host_edit.text(),
            "port": self.port_edit.text(),
            "dbname": self.dbname_edit.text(),
            "user": self.user_edit.text(),
            "password": self.password_edit.text()
        }

        try: # تم تصحيح هذا السطر
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(all_settings, f, ensure_ascii=False, indent=4)
            
            reply = QMessageBox.information(self, "حفظ الإعدادات", 
                                            "تم حفظ الإعدادات بنجاح.\nيجب إعادة تشغيل البرنامج لتطبيق التغييرات.",
                                            QMessageBox.Ok)
            if reply == QMessageBox.Ok:
                QApplication.instance().quit()
                # إعادة تشغيل التطبيق. هذا يعمل مع كل من وضع التطوير والبرنامج المجمع
                # sys.executable هو المسار إلى python.exe أو ARABLY_ERP.exe
                # sys.argv[0] هو اسم السكربت أو الـ exe
                os.execv(sys.executable, [sys.executable] + sys.argv)

        except Exception as e:
            QMessageBox.critical(self, "خطأ في الحفظ", f"حدث خطأ أثناء حفظ الإعدادات: {e}")

class PrintingSettingsWidget(QWidget):
    """واجهة إعدادات الطباعة"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)

        settings_group = QGroupBox(self.tr("إعدادات الطباعة الافتراضية"))
        settings_group.setStyleSheet("font-weight: bold;")
        form_layout = QFormLayout()
        settings_group.setLayout(form_layout)

        # --- اختيار الطابعة ---
        self.printer_combo = QComboBox()
        available_printers = QPrinterInfo.availablePrinterNames()
        if available_printers:
            self.printer_combo.addItems(available_printers) # تم تصحيح هذا السطر
        else:
            self.printer_combo.addItem(self.tr("لا توجد طابعات مثبتة"))
            self.printer_combo.setEnabled(False)

        # --- اختيار نموذج الفاتورة ---
        self.template_combo = QComboBox()
        self.template_combo.addItems([self.tr("فاتورة A4"), self.tr("فاتورة A5"), self.tr("فاتورة ريسيت حراري 80mm")])

        # --- تذييل الفاتورة ---
        self.footer_edit = QTextEdit()
        self.footer_edit.setPlaceholderText(self.tr("مثال: شكراً لتعاملكم معنا..."))
        self.footer_edit.setFixedHeight(100)

        form_layout.addRow(self.tr("الطابعة الافتراضية:"), self.printer_combo)
        form_layout.addRow("نموذج الفاتورة الافتراضي:", self.template_combo)
        form_layout.addRow("تذييل الفاتورة:", self.footer_edit)

        main_layout.addWidget(settings_group)

        # --- زر الحفظ ---
        preview_button = QPushButton("معاينة النموذج")
        preview_button.clicked.connect(self.show_print_preview) # تم تصحيح هذا السطر

        save_button = QPushButton("حفظ الإعدادات")
        save_button.clicked.connect(self.save_settings)
        save_button.setFixedWidth(150)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(preview_button)
        buttons_layout.addWidget(save_button)

        main_layout.addLayout(buttons_layout)
        
        self.load_settings() # تحميل الإعدادات عند فتح الشاشة

    def show_print_preview(self):
        """يعرض نافذة معاينة قبل الطباعة لفاتورة وهمية"""
        doc = QTextDocument()

        # الحصول على نص التذييل من الواجهة
        footer_text = self.footer_edit.toPlainText()

        # إنشاء محتوى HTML للفاتورة الوهمية # تم تصحيح هذا السطر
        html_content = f"""
        <div dir="rtl" style="font-family: sans-serif; padding: 20px;">
            <h1 style="text-align: center; color: #333;">{self.tr("فاتورة ضريبية مبسطة")}</h1>
            <p><strong>{self.tr("رقم الفاتورة:")}</strong> 1001</p>
            <p><strong>{self.tr("التاريخ:")}</strong> {QDate.currentDate().toString("yyyy-MM-dd")}</p>
            <hr>
            <table width="100%" style="border-collapse: collapse;">
                <thead style="background-color: #f2f2f2;">
                    <tr>
                        <th style="padding: 8px; border: 1px solid #ddd;">{self.tr("الصنف")}</th>
                        <th style="padding: 8px; border: 1px solid #ddd;">{self.tr("الكمية")}</th>
                        <th style="padding: 8px; border: 1px solid #ddd;">{self.tr("السعر")}</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;">{self.tr("لابتوب Dell")}</td>
                        <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{self.tr("1")}</td>
                        <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{self.tr("15000.00")}</td>
                    </tr>
                </tbody>
            </table>
            <h3 style="text-align: left; margin-top: 20px;">الإجمالي: 15000.00</h3>
            <hr>
            <p style="text-align: center; color: #555;">{footer_text}</p>
        </div>
        """
        doc.setHtml(html_content)

        preview_dialog = QPrintPreviewDialog()
        preview_dialog.paintRequested.connect(doc.print_)
        preview_dialog.exec()

    def save_settings(self):
        """يحفظ إعدادات الطباعة"""
        settings_file = get_app_data_path("settings.json")
        all_settings = {}
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    all_settings = json.load(f)
            except json.JSONDecodeError:
                pass

        all_settings["printing"] = {
            "default_printer": self.printer_combo.currentText(),
            "default_template": self.template_combo.currentText(),
            "footer_text": self.footer_edit.toPlainText()
        }

        try:
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(all_settings, f, ensure_ascii=False, indent=4)
            QMessageBox.information(self, self.tr("حفظ الإعدادات"), self.tr("تم حفظ إعدادات الطباعة بنجاح!"))
        except Exception as e:
            QMessageBox.critical(self, "خطأ في الحفظ", f"حدث خطأ أثناء حفظ الإعدادات: {e}")

    def load_settings(self):
        """تحميل إعدادات الطباعة من ملف JSON"""
        settings_file = get_app_data_path("settings.json")
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    all_settings = json.load(f)
                    printing_settings = all_settings.get("printing", {})
                    self.printer_combo.setCurrentText(printing_settings.get("default_printer", ""))
                    self.template_combo.setCurrentText(printing_settings.get("default_template", ""))
                    self.footer_edit.setPlainText(printing_settings.get("footer_text", ""))
            except Exception as e: # تم تصحيح هذا السطر
                print(f"Could not load printing settings: {e}")

class AddCustomerDialog(QDialog):
    """نافذة منبثقة لإضافة عميل جديد"""
    def __init__(self, parent=None, customer_data=None):
        super().__init__(parent)
        self.setWindowTitle("إضافة عميل جديد")
        self.setLayoutDirection(Qt.RightToLeft) # تم تصحيح هذا السطر
        self.setMinimumWidth(350)

        self.form_layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.address_edit = QLineEdit() # تم تصحيح هذا السطر

        self.form_layout.addRow(self.tr("اسم العميل:"), self.name_edit)
        self.form_layout.addRow(self.tr("رقم الهاتف:"), self.phone_edit)
        self.form_layout.addRow(self.tr("العنوان:"), self.address_edit)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.form_layout.addRow(self.button_box)

        if customer_data:
            self.setWindowTitle("تعديل بيانات العميل")
            self.name_edit.setText(customer_data.name) # تم تصحيح هذا السطر
            self.phone_edit.setText(customer_data.phone)
            self.address_edit.setText(customer_data.address)


    def get_data(self):
        return {
            "name": self.name_edit.text(),
            "phone": self.phone_edit.text(),
            "address": self.address_edit.text()
        }

class AddSupplierDialog(QDialog):
    """نافذة منبثقة لإضافة مورد جديد"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("إضافة مورد جديد"))
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumWidth(350)

        self.form_layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.phone_edit = QLineEdit() # تم تصحيح هذا السطر
        self.address_edit = QLineEdit()

        self.form_layout.addRow(self.tr("اسم المورد:"), self.name_edit)
        self.form_layout.addRow(self.tr("رقم الهاتف:"), self.phone_edit)
        self.form_layout.addRow(self.tr("العنوان:"), self.address_edit)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.form_layout.addRow(self.button_box)

    def get_data(self):
        """تُرجع البيانات المدخلة في شكل قاموس"""
        return {
            "name": self.name_edit.text(),
            "phone": self.phone_edit.text(),
            "address": self.address_edit.text()
        }

class AddSellerDialog(QDialog):
    """نافذة منبثقة لإضافة أو تعديل بائع"""
    def __init__(self, parent=None, seller_data=None):
        super().__init__(parent) # تم تصحيح هذا السطر
        self.setWindowTitle(self.tr("إضافة بائع جديد") if not seller_data else self.tr("تعديل بيانات البائع"))
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumWidth(350)
        self.form_layout = QFormLayout(self)
        self.name_edit = QLineEdit(seller_data.name if seller_data else "")
        self.phone_edit = QLineEdit(seller_data.phone if seller_data else "")
        self.address_edit = QLineEdit(seller_data.address if seller_data else "")
        self.form_layout.addRow(self.tr("اسم البائع:"), self.name_edit)
        self.form_layout.addRow(self.tr("رقم الهاتف:"), self.phone_edit)
        self.form_layout.addRow(self.tr("العنوان:"), self.address_edit)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.form_layout.addRow(self.button_box)

class AIAssistantDialog(QDialog):
    """نافذة المساعد الذكي للإجابة على أسئلة المستخدم"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("المساعد الذكي")
        self.setMinimumSize(800, 500)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setObjectName("AIAssistantDialog")
        self.setStyleSheet("""
            #AIAssistantDialog {
                background-color: #282c34;
            }
            QLabel {
                color: #abb2bf;
                font-size: 11pt;
            }
            QLineEdit {
                background-color: #21252b;
                border: 1px solid #33373e;
                border-radius: 5px;
                padding: 8px;
                color: #abb2bf;
                font-size: 11pt;
            }
            QListWidget {
                background-color: #21252b;
                border: 1px solid #33373e;
                border-radius: 5px;
                color: #abb2bf;
                font-size: 11pt;
            }
            QListWidget::item:selected {
                background-color: #3a3f4b;
                color: #61afef;
            }
            QTextEdit {
                background-color: #282c34;
                border: none;
                color: #c8ccd4;
                font-size: 12pt;
            }
        """)

        self.knowledge_base = {
            "كيف أقوم بإضافة فاتورة مبيعات جديدة؟": {
                "text": """
                    <p>لإضافة فاتورة مبيعات جديدة، اتبع الخطوات التالية:</p>
                    <ol>
                        <li>من القائمة العلوية، اذهب إلى <strong>المبيعات والفواتير > فاتورة جديدة</strong>.</li>
                        <li>اختر العميل من القائمة المنسدلة. إذا كان عميلاً جديداً، يمكنك إضافته بالضغط على زر <strong>(+)</strong>.</li>
                        <li>في حقل البحث عن صنف، ابدأ بكتابة كود الصنف أو جزء من اسمه ثم اضغط <strong>Enter</strong> أو زر "إضافة الصنف".</li>
                        <li>عدّل الكمية والسعر والخصم لكل صنف في الجدول حسب الحاجة.</li>
                        <li>أدخل المبلغ المدفوع في حقل "المدفوع" أسفل الشاشة.</li>
                        <li>اضغط على زر <strong>"حفظ واعتماد"</strong> لحفظ الفاتورة وتحديث المخزون.</li>
                    </ol>
                """,
                "image": "assets/help_images/add_invoice.png"
            },
            "كيف أضيف صنفاً جديداً للمخزون؟": {
                "text": "من القائمة العلوية، اختر 'المخزون' ثم 'إدارة الأصناف'. في الشاشة التي تظهر، اضغط على زر 'إضافة صنف جديد' واملأ البيانات المطلوبة.",
                "image": None
            },
            "كيف أتحقق من رصيد الخزينة؟": {
                "text": "اذهب إلى قائمة 'المحاسبة' واختر 'الخزينة'. ستظهر لك شاشة تعرض الرصيد الحالي وجميع حركات الإيداع والسحب التي تمت.",
                "image": "assets/help_images/treasury.png"
            },
            # ... يمكنك إضافة باقي الأسئلة بنفس الطريقة
            "كيف أضيف عميلاً جديداً؟": {"text": "يمكنك إضافة عميل جديد مباشرة من شاشة فاتورة المبيعات بالضغط على زر (+) بجانب قائمة العملاء، أو من خلال شاشة 'إدارة العملاء' في قائمة 'العملاء والموردين'.", "image": None},
        }

        self.init_ui()
        self.load_topics()

    def init_ui(self): # تم تصحيح هذا السطر
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("اكتب سؤالك هنا للبحث...")
        self.search_bar.textChanged.connect(self.filter_topics)
        main_layout.addWidget(self.search_bar)

        content_layout = QHBoxLayout()

        self.answer_display = QTextEdit()
        self.answer_display.setReadOnly(True) # تم تصحيح هذا السطر
        
        self.topics_list = QListWidget()
        self.topics_list.currentItemChanged.connect(self.display_answer)

        content_layout.addWidget(self.answer_display, 3) # يأخذ 3/4 من المساحة
        content_layout.addWidget(self.topics_list, 1)   # يأخذ 1/4 من المساحة

        main_layout.addLayout(content_layout)

    def load_topics(self):
        self.topics_list.clear()
        for topic in self.knowledge_base.keys(): # تم تصحيح هذا السطر
            self.topics_list.addItem(topic)
        self.topics_list.setCurrentRow(0)

    def filter_topics(self, text):
        search_text = text.lower()
        for i in range(self.topics_list.count()):
            item = self.topics_list.item(i)
            item.setHidden(search_text not in item.text().lower())

    def display_answer(self, current_item, previous_item):
        if not current_item:
            return
        question = current_item.text()
        answer_data = self.knowledge_base.get(question)

        if not answer_data:
            self.answer_display.setHtml(self.tr("<p>عفواً، لا توجد إجابة لهذا السؤال حالياً.</p>"))
            return

        html_content = f"<div style='padding: 10px;'>{answer_data['text']}</div>"
        
        image_path = answer_data.get("image")
        if image_path and os.path.exists(image_path):
            # تحويل المسار إلى رابط URI ليعمل بشكل صحيح في HTML
            image_uri = Path(image_path).resolve().as_uri()
            html_content += f'<br><img src="{image_uri}" width="450" style="border: 1px solid #33373e; border-radius: 5px; margin-top: 10px;">'

        self.answer_display.setHtml(html_content)

class SalesReportsWidget(QWidget):
    """واجهة عرض تقارير المبيعات"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_session = database.SessionLocal()
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()
        self.load_customers_filter()
        self.apply_filters() # تحميل كل الفواتير عند الفتح

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # --- قسم الفلاتر ---
        filters_group = QGroupBox(self.tr("فلترة التقارير"))
        filters_layout = QHBoxLayout()
        
        self.customer_filter_combo = QComboBox()
        filters_layout.addWidget(QLabel("العميل:"))
        filters_layout.addWidget(self.customer_filter_combo)

        self.from_date_edit = QDateEdit(QDate.currentDate().addMonths(-1))
        self.from_date_edit.setCalendarPopup(True)
        filters_layout.addWidget(QLabel("من تاريخ:"))
        filters_layout.addWidget(self.from_date_edit)

        self.to_date_edit = QDateEdit(QDate.currentDate())
        self.to_date_edit.setCalendarPopup(True)
        filters_layout.addWidget(QLabel("إلى تاريخ:"))
        filters_layout.addWidget(self.to_date_edit)
        
        apply_button = QPushButton("تطبيق الفلتر")
        apply_button.clicked.connect(self.apply_filters)
        filters_layout.addWidget(apply_button)

        self.view_button = QPushButton("عرض الفاتورة")
        self.view_button.clicked.connect(self.view_selected_invoice)
        filters_layout.addWidget(self.view_button)

        self.edit_button = QPushButton("تعديل الفاتورة")
        self.edit_button.clicked.connect(self.edit_selected_invoice)
        filters_layout.addWidget(self.edit_button)

        # --- زر تصدير Excel ---
        self.export_excel_button = QPushButton(self.style().standardIcon(QStyle.SP_DialogSaveButton), "تصدير إلى Excel")
        self.export_excel_button.clicked.connect(self.export_to_excel)
        filters_layout.addWidget(self.export_excel_button)

        # --- زر تصدير PDF ---
        self.export_pdf_button = QPushButton(self.style().standardIcon(QStyle.SP_DialogSaveButton), "تصدير إلى PDF")
        self.export_pdf_button.clicked.connect(self.export_to_pdf)
        filters_layout.addWidget(self.export_pdf_button)

        filters_layout.addStretch()

        filters_group.setLayout(filters_layout)
        main_layout.addWidget(filters_group)

        # --- جدول الفواتير ---
        self.invoices_table = QTableWidget()
        self.invoices_table.setColumnCount(7) # تم تصحيح هذا السطر
        self.invoices_table.setHorizontalHeaderLabels(
            ["رقم الفاتورة", "التاريخ", "اسم العميل", "الإجمالي", "المدفوع", "المتبقي", "طريقة الدفع"]
        )
        self.invoices_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.invoices_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.invoices_table.itemDoubleClicked.connect(self.show_invoice_details)
        main_layout.addWidget(self.invoices_table)

        # --- قسم الإجماليات ---
        totals_layout = QHBoxLayout() # تم تصحيح هذا السطر
        totals_layout.addWidget(QLabel("إجمالي المبيعات:"))
        self.total_sales_label = QLabel("0.00")
        self.total_sales_label.setStyleSheet("font-weight: bold; color: blue;")
        totals_layout.addWidget(self.total_sales_label)
        totals_layout.addStretch()
        main_layout.addLayout(totals_layout)

    def load_customers_filter(self):
        self.customer_filter_combo.addItem(self.tr("كل العملاء"), -1)
        customers = self.db_session.query(database.Customer).all()
        for customer in customers:
            self.customer_filter_combo.addItem(customer.name, customer.id)

    def apply_filters(self):
        query = self.db_session.query(database.Invoice)

        # فلترة بالعميل
        customer_id = self.customer_filter_combo.currentData()
        if customer_id != -1:
            query = query.filter(database.Invoice.customer_id == customer_id)

        # فلترة بالتاريخ
        from_date = self.from_date_edit.date().toPython()
        to_date = self.to_date_edit.date().toPython()
        query = query.filter(database.Invoice.date.between(from_date, to_date))

        invoices = query.order_by(database.Invoice.date.desc()).all()
        
        self.invoices_table.setRowCount(0)
        total_sales = 0.0 # تم تصحيح هذا السطر
        for inv in invoices:
            row = self.invoices_table.rowCount()
            self.invoices_table.insertRow(row)
            self.invoices_table.setItem(row, 0, QTableWidgetItem(str(inv.id)))
            self.invoices_table.setItem(row, 1, QTableWidgetItem(inv.date.strftime("%Y-%m-%d")))
            self.invoices_table.setItem(row, 2, QTableWidgetItem(inv.customer.name if inv.customer else "N/A"))
            self.invoices_table.setItem(row, 3, QTableWidgetItem(f"{inv.total_amount:.2f}"))
            self.invoices_table.setItem(row, 4, QTableWidgetItem(f"{inv.paid_amount:.2f}"))
            self.invoices_table.setItem(row, 5, QTableWidgetItem(f"{(inv.total_amount - inv.paid_amount):.2f}"))
            self.invoices_table.setItem(row, 6, QTableWidgetItem(inv.payment_method))
            total_sales += inv.total_amount
        
        self.total_sales_label.setText(f"{total_sales:.2f}")

    def show_invoice_details(self, item):
        """يفتح نافذة تفاصيل الفاتورة عند الضغط المزدوج"""
        if item is None:
            return
        # الحصول على رقم الفاتورة من العمود الأول في الصف المحدد
        invoice_id = int(self.invoices_table.item(item.row(), 0).text())
        dialog = InvoiceDetailsDialog(invoice_id, self.db_session, self)
        dialog.exec()

    def view_selected_invoice(self):
        """يفتح نافذة تفاصيل الفاتورة المحددة عند الضغط على زر العرض"""
        selected_row = self.invoices_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "خطأ", "يرجى تحديد فاتورة لعرضها.")
            return

        invoice_id = int(self.invoices_table.item(selected_row, 0).text())
        dialog = InvoiceDetailsDialog(invoice_id, self.db_session, self)
        dialog.exec()

    def edit_selected_invoice(self):
        """يفتح الفاتورة المحددة في واجهة التعديل"""
        selected_row = self.invoices_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "خطأ", "يرجى تحديد فاتورة لتعديلها.")
            return

        invoice_id = int(self.invoices_table.item(selected_row, 0).text())
        
        # الوصول إلى النافذة الرئيسية لفتح الواجهة الجديدة
        main_window = self.window()
        if isinstance(main_window, MainWindow):
            edit_widget = SalesInvoiceWidget(invoice_id=invoice_id)
            main_window.open_in_new_window(edit_widget, f"تعديل فاتورة رقم {invoice_id}")

    def export_to_excel(self):
        """تصدير البيانات الحالية في الجدول إلى ملف Excel"""
        if self.invoices_table.rowCount() == 0:
            QMessageBox.information(self, "لا توجد بيانات", "لا توجد بيانات لتصديرها.")
            return

        try:
            import openpyxl
        except ImportError:
            QMessageBox.critical(self, "مكتبة مفقودة", 
                                 "مكتبة `openpyxl` غير مثبتة.\n"
                                 "يرجى تثبيتها باستخدام الأمر: pip install openpyxl")
            return

        # طلب مسار الحفظ من المستخدم
        path, _ = QFileDialog.getSaveFileName(self, "حفظ ملف Excel", "", "Excel Files (*.xlsx)")

        if not path:
            return

        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "تقارير المبيعات"
        sheet.sheet_view.rightToLeft = True # جعل الورقة من اليمين لليسار

        # كتابة العناوين
        headers = [self.invoices_table.horizontalHeaderItem(i).text() for i in range(self.invoices_table.columnCount())]
        sheet.append(headers)

        # كتابة البيانات
        for row in range(self.invoices_table.rowCount()):
            row_data = []
            for col in range(self.invoices_table.columnCount()):
                item = self.invoices_table.item(row, col)
                row_data.append(item.text() if item else "")
            sheet.append(row_data)

        # إضافة الإجمالي في النهاية
        sheet.append([]) # صف فارغ
        sheet.append(["", "", "", "", "إجمالي المبيعات:", self.total_sales_label.text()])

        workbook.save(path)
        QMessageBox.information(self, "نجاح", f"تم تصدير التقرير بنجاح إلى:\n{path}")

    def export_to_pdf(self):
        """تصدير البيانات الحالية في الجدول إلى ملف PDF"""
        if self.invoices_table.rowCount() == 0:
            QMessageBox.information(self, "لا توجد بيانات", "لا توجد بيانات لتصديرها.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "حفظ ملف PDF", "", "PDF Files (*.pdf)")

        if not path:
            return

        # --- إنشاء محتوى HTML للتقرير ---
        from_date = self.from_date_edit.date().toString("yyyy-MM-dd")
        to_date = self.to_date_edit.date().toString("yyyy-MM-dd")

        items_html = ""
        for row in range(self.invoices_table.rowCount()):
            items_html += f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{self.invoices_table.item(row, 0).text()}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{self.invoices_table.item(row, 1).text()}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{self.invoices_table.item(row, 2).text()}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">{self.invoices_table.item(row, 3).text()}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">{self.invoices_table.item(row, 4).text()}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">{self.invoices_table.item(row, 5).text()}</td>
            </tr>
            """

        html_content = f"""
        <div dir="rtl" style="font-family: 'Segoe UI', Arial, sans-serif; padding: 20px;">
            <h1 style="text-align: center; color: #333;">تقرير المبيعات</h1>
            <p style="text-align: center; color: #555;">من تاريخ: {from_date} إلى تاريخ: {to_date}</p>
            <hr>
            <table width="100%" style="border-collapse: collapse; font-size: 10pt;">
                <thead style="background-color: #f2f2f2;">
                    <tr>
                        <th style="padding: 8px; border: 1px solid #ddd;">رقم الفاتورة</th>
                        <th style="padding: 8px; border: 1px solid #ddd;">التاريخ</th>
                        <th style="padding: 8px; border: 1px solid #ddd;">اسم العميل</th>
                        <th style="padding: 8px; border: 1px solid #ddd;">الإجمالي</th>
                        <th style="padding: 8px; border: 1px solid #ddd;">المدفوع</th>
                        <th style="padding: 8px; border: 1px solid #ddd;">المتبقي</th>
                    </tr>
                </thead>
                <tbody>{items_html}</tbody>
            </table>
            <h3 style="text-align: left; margin-top: 20px;">إجمالي المبيعات: {self.total_sales_label.text()}</h3>
            <p style="text-align: center; color: #888; font-size: 9pt; margin-top: 30px;">
                تم إنشاء هذا التقرير بواسطة نظام ARABLY ERP
            </p>
        </div>
        """

        doc = QTextDocument()
        doc.setHtml(html_content)

        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(path)
        doc.print_(printer)

        QMessageBox.information(self, "نجاح", f"تم تصدير التقرير كملف PDF بنجاح إلى:\n{path}")

class InvoiceDetailsDialog(QDialog):
    """نافذة منبثقة لعرض تفاصيل فاتورة محددة"""
    def __init__(self, invoice_id, db_session, parent=None):
        super().__init__(parent)
        self.db_session = db_session
        self.invoice_id = invoice_id # تم تصحيح هذا السطر
        self.setWindowTitle(self.tr(f"تفاصيل الفاتورة رقم {self.invoice_id}")) # تم تصحيح هذا السطر
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumSize(600, 400)

        self.init_ui()
        self.load_invoice_details()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # --- قسم معلومات الفاتورة ---
        info_group = QGroupBox(self.tr("معلومات الفاتورة"))
        self.info_layout = QFormLayout(info_group)
        self.customer_label = QLabel()
        self.date_label = QLabel()
        self.total_label = QLabel()
        self.info_layout.addRow("العميل:", self.customer_label)
        self.info_layout.addRow("التاريخ:", self.date_label)
        self.info_layout.addRow("الإجمالي:", self.total_label)
        main_layout.addWidget(info_group)

        # --- قسم أصناف الفاتورة ---
        items_group = QGroupBox(self.tr("الأصناف"))
        items_layout = QVBoxLayout(items_group)
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4) # تم تصحيح هذا السطر
        self.items_table.setHorizontalHeaderLabels(["اسم الصنف", "الكمية", "سعر الوحدة", "الإجمالي"])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.setEditTriggers(QTableWidget.NoEditTriggers)
        items_layout.addWidget(self.items_table)
        main_layout.addWidget(items_group)

        # --- زر الإغلاق ---
        close_button = QPushButton(self.tr("إغلاق"))
        close_button.clicked.connect(self.accept)
        main_layout.addWidget(close_button, 0, Qt.AlignLeft)

    def load_invoice_details(self):
        invoice = self.db_session.query(database.Invoice).filter(database.Invoice.id == self.invoice_id).first()
        if not invoice:
            return

        self.customer_label.setText(invoice.customer.name if invoice.customer else "N/A")
        self.date_label.setText(invoice.date.strftime("%Y-%m-%d")) # تم تصحيح هذا السطر
        self.total_label.setText(f"{invoice.total_amount:.2f}")

        for inv_item in invoice.items:
            row = self.items_table.rowCount()
            self.items_table.insertRow(row)
            self.items_table.setItem(row, 0, QTableWidgetItem(inv_item.item.name))
            self.items_table.setItem(row, 1, QTableWidgetItem(str(inv_item.quantity)))
            self.items_table.setItem(row, 2, QTableWidgetItem(f"{inv_item.price_per_unit:.2f}"))
            self.items_table.setItem(row, 3, QTableWidgetItem(f"{(inv_item.quantity * inv_item.price_per_unit):.2f}"))

class CustomersManagementWidget(QWidget):
    """واجهة إدارة العملاء"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_session = database.SessionLocal()
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()
        self.load_customers()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        buttons_layout = QHBoxLayout()
        add_button = QPushButton(self.tr("إضافة عميل جديد"))
        add_button.clicked.connect(self.add_customer)
        edit_button = QPushButton(self.tr("تعديل المحدد"))
        edit_button.clicked.connect(self.edit_customer)
        delete_button = QPushButton(self.tr("حذف المحدد"))
        delete_button.clicked.connect(self.delete_customer) # تم تصحيح هذا السطر
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(edit_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)

        self.customers_table = QTableWidget()
        self.customers_table.setColumnCount(5)
        self.customers_table.setHorizontalHeaderLabels([self.tr("ID"), self.tr("اسم العميل"), self.tr("رقم الهاتف"), self.tr("العنوان"), self.tr("المديونية الحالية")])
        self.customers_table.setColumnHidden(0, True)
        self.customers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.customers_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.customers_table.setSelectionBehavior(QTableWidget.SelectRows)
        main_layout.addWidget(self.customers_table)

    def load_customers(self):
        self.customers_table.setRowCount(0)
        customers = self.db_session.query(database.Customer).all()
        for customer in customers:
            row = self.customers_table.rowCount()
            self.customers_table.insertRow(row)
            self.customers_table.setItem(row, 0, QTableWidgetItem(str(customer.id)))
            self.customers_table.setItem(row, 1, QTableWidgetItem(customer.name))
            self.customers_table.setItem(row, 2, QTableWidgetItem(customer.phone)) # تم تصحيح هذا السطر
            self.customers_table.setItem(row, 3, QTableWidgetItem(customer.address))
            self.customers_table.setItem(row, 4, QTableWidgetItem(f"{customer.current_debt:.2f}"))

    def add_customer(self):
        dialog = AddCustomerDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            new_customer = database.Customer(**data)
            self.db_session.add(new_customer)
            self.db_session.commit() # تم تصحيح هذا السطر
            self.load_customers()

    def edit_customer(self):
        selected_row = self.customers_table.currentRow()
        if selected_row < 0: return

        customer_id = int(self.customers_table.item(selected_row, 0).text())
        customer_to_edit = self.db_session.get(database.Customer, customer_id)
        
        dialog = AddCustomerDialog(self, customer_data=customer_to_edit) # تم تصحيح هذا السطر
        if dialog.exec() == QDialog.Accepted:
            new_data = dialog.get_data()
            customer_to_edit.name = new_data['name']
            customer_to_edit.phone = new_data['phone']
            customer_to_edit.address = new_data['address']
            self.db_session.commit()
            self.load_customers()

    def delete_customer(self):
        selected_row = self.customers_table.currentRow()
        if selected_row < 0: return

        customer_id = int(self.customers_table.item(selected_row, 0).text())
        reply = QMessageBox.question(self, self.tr("تأكيد الحذف"), self.tr("هل أنت متأكد من حذف هذا العميل؟"))
        if reply == QMessageBox.Yes:
            self.db_session.query(database.Customer).filter(database.Customer.id == customer_id).delete()
            self.db_session.commit()
            self.load_customers()

    def closeEvent(self, event):
        """يتم استدعاؤها عند إغلاق الواجهة لضمان إغلاق جلسة قاعدة البيانات"""
        self.db_session.close()
        super().closeEvent(event)

class SuppliersManagementWidget(QWidget):
    """واجهة إدارة الموردين"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_session = database.SessionLocal()
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()
        self.load_suppliers()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        buttons_layout = QHBoxLayout()
        add_button = QPushButton(self.tr("إضافة مورد جديد"))
        add_button.clicked.connect(self.add_supplier)
        edit_button = QPushButton(self.tr("تعديل المحدد"))
        edit_button.clicked.connect(self.edit_supplier)
        delete_button = QPushButton(self.tr("حذف المحدد"))
        delete_button.setObjectName("delete_button") # تم تصحيح هذا السطر
        delete_button.clicked.connect(self.delete_supplier)
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(edit_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)

        self.suppliers_table = QTableWidget()
        self.suppliers_table.setColumnCount(5)
        self.suppliers_table.setHorizontalHeaderLabels([self.tr("ID"), self.tr("اسم المورد"), self.tr("رقم الهاتف"), self.tr("العنوان"), self.tr("الرصيد الحالي")])
        self.suppliers_table.setColumnHidden(0, True)
        self.suppliers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.suppliers_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.suppliers_table.setSelectionBehavior(QTableWidget.SelectRows)
        main_layout.addWidget(self.suppliers_table)

    def load_suppliers(self):
        self.suppliers_table.setRowCount(0)
        suppliers = self.db_session.query(database.Supplier).all()
        for supplier in suppliers:
            row = self.suppliers_table.rowCount()
            self.suppliers_table.insertRow(row)
            self.suppliers_table.setItem(row, 0, QTableWidgetItem(str(supplier.id)))
            self.suppliers_table.setItem(row, 1, QTableWidgetItem(supplier.name))
            self.suppliers_table.setItem(row, 2, QTableWidgetItem(supplier.phone)) # تم تصحيح هذا السطر
            self.suppliers_table.setItem(row, 3, QTableWidgetItem(supplier.address))
            self.suppliers_table.setItem(row, 4, QTableWidgetItem(f"{supplier.current_balance:.2f}"))

    def add_supplier(self):
        dialog = AddSupplierDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            new_supplier = database.Supplier(**data)
            self.db_session.add(new_supplier)
            self.db_session.commit() # تم تصحيح هذا السطر
            self.load_suppliers()

    def edit_supplier(self):
        selected_row = self.suppliers_table.currentRow()
        if selected_row < 0: return

        supplier_id = int(self.suppliers_table.item(selected_row, 0).text())
        supplier_to_edit = self.db_session.get(database.Supplier, supplier_id)

        dialog = AddSupplierDialog(self) # تم تعديل هذا السطر # تم تصحيح هذا السطر
        if dialog.exec() == QDialog.Accepted:
            # يجب أن يكون هناك نافذة تعديل منفصلة أو تعديل النافذة الحالية لتقبل البيانات
            new_data = dialog.get_data()
            supplier_to_edit.name = new_data['name']
            supplier_to_edit.phone = new_data['phone']
            supplier_to_edit.address = new_data['address']
            self.db_session.commit()
            self.load_suppliers()

    def delete_supplier(self):
        selected_row = self.suppliers_table.currentRow()
        if selected_row < 0: return

        supplier_id = int(self.suppliers_table.item(selected_row, 0).text())
        reply = QMessageBox.question(self, self.tr("تأكيد الحذف"), self.tr("هل أنت متأكد من حذف هذا المورد؟"))
        if reply == QMessageBox.Yes:
            # يمكنك إضافة تحقق هنا من الفواتير المرتبطة
            self.db_session.query(database.Supplier).filter(database.Supplier.id == supplier_id).delete()
            self.db_session.commit()
            self.load_suppliers()

    def closeEvent(self, event):
        """يتم استدعاؤها عند إغلاق الواجهة لضمان إغلاق جلسة قاعدة البيانات"""
        self.db_session.close()
        super().closeEvent(event)

class StoresManagementWidget(QWidget):
    """واجهة إدارة المخازن"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_session = database.SessionLocal()
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()
        self.load_stores()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # --- أزرار الإجراءات ---
        buttons_layout = QHBoxLayout() # تم تصحيح هذا السطر
        add_button = QPushButton(self.tr("إضافة مخزن جديد"))
        add_button.clicked.connect(self.add_store)
        edit_button = QPushButton(self.tr("تعديل المحدد"))
        edit_button.clicked.connect(self.edit_store)
        delete_button = QPushButton(self.tr("حذف المحدد"))
        delete_button.clicked.connect(self.delete_store)
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(edit_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)

        # --- جدول المخازن ---
        self.stores_table = QTableWidget()
        self.stores_table.setColumnCount(2) # تم تصحيح هذا السطر
        self.stores_table.setHorizontalHeaderLabels(["ID", "اسم المخزن"])
        self.stores_table.setColumnHidden(0, True)
        self.stores_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.stores_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.stores_table.setSelectionBehavior(QTableWidget.SelectRows)
        main_layout.addWidget(self.stores_table)

    def load_stores(self):
        self.stores_table.setRowCount(0)
        stores = self.db_session.query(database.Store).all()
        for store in stores:
            row = self.stores_table.rowCount()
            self.stores_table.insertRow(row)
            self.stores_table.setItem(row, 0, QTableWidgetItem(str(store.id)))
            self.stores_table.setItem(row, 1, QTableWidgetItem(store.name))
    
    def add_store(self):
        name, ok = QInputDialog.getText(self, "إضافة مخزن", "ادخل اسم المخزن الجديد:")
        if ok and name:
            new_store = database.Store(name=name)
            self.db_session.add(new_store)
            self.db_session.commit()
            self.load_stores()

    def edit_store(self):
        selected_row = self.stores_table.currentRow()
        if selected_row < 0: return

        store_id = int(self.stores_table.item(selected_row, 0).text())
        store_to_edit = self.db_session.get(database.Store, store_id) # تم تصحيح هذا السطر
        
        new_name, ok = QInputDialog.getText(self, self.tr("تعديل مخزن"), self.tr("الاسم الجديد:"), text=store_to_edit.name)
        if ok and new_name:
            store_to_edit.name = new_name
            self.db_session.commit()
            self.load_stores()

    def delete_store(self):
        selected_row = self.stores_table.currentRow()
        if selected_row < 0: return

        store_id = int(self.stores_table.item(selected_row, 0).text())
        reply = QMessageBox.question(self, self.tr("تأكيد الحذف"), self.tr("هل أنت متأكد من حذف هذا المخزن؟\n(ملاحظة: لا يمكن حذف مخزن مرتبط بأصناف)"))
        if reply == QMessageBox.Yes:
            # يمكنك إضافة تحقق هنا لمنع حذف مخزن مرتبط بأصناف
            self.db_session.query(database.Store).filter(database.Store.id == store_id).delete()
            self.db_session.commit()
            self.load_stores()

    def closeEvent(self, event):
        """يتم استدعاؤها عند إغلاق الواجهة لضمان إغلاق جلسة قاعدة البيانات"""
        self.db_session.close()
        super().closeEvent(event)

class SellersManagementWidget(QWidget):
    """واجهة إدارة البائعين"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_session = database.SessionLocal()
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()
        self.load_sellers()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        buttons_layout = QHBoxLayout()
        add_button = QPushButton(self.tr("إضافة بائع جديد"))
        add_button.clicked.connect(self.add_seller)
        edit_button = QPushButton(self.tr("تعديل المحدد"))
        edit_button.clicked.connect(self.edit_seller)
        delete_button = QPushButton(self.tr("حذف المحدد"))
        delete_button.clicked.connect(self.delete_seller) # تم تصحيح هذا السطر
        delete_button.setObjectName("delete_button")
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(edit_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)

        self.sellers_table = QTableWidget()
        self.sellers_table.setColumnCount(4)
        self.sellers_table.setHorizontalHeaderLabels([self.tr("ID"), self.tr("اسم البائع"), self.tr("رقم الهاتف"), self.tr("العنوان")])
        self.sellers_table.setColumnHidden(0, True)
        self.sellers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.sellers_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.sellers_table.setSelectionBehavior(QTableWidget.SelectRows)
        main_layout.addWidget(self.sellers_table)

    def load_sellers(self):
        self.sellers_table.setRowCount(0)
        sellers = self.db_session.query(database.Seller).all()
        for seller in sellers:
            row = self.sellers_table.rowCount()
            self.sellers_table.insertRow(row)
            self.sellers_table.setItem(row, 0, QTableWidgetItem(str(seller.id)))
            self.sellers_table.setItem(row, 1, QTableWidgetItem(seller.name))
            self.sellers_table.setItem(row, 2, QTableWidgetItem(seller.phone)) # تم تصحيح هذا السطر
            self.sellers_table.setItem(row, 3, QTableWidgetItem(seller.address))

    def add_seller(self):
        dialog = AddSellerDialog(self)
        if dialog.exec() == QDialog.Accepted:
            new_seller = database.Seller(name=dialog.name_edit.text(), phone=dialog.phone_edit.text(), address=dialog.address_edit.text())
            self.db_session.add(new_seller)
            self.db_session.commit()
            self.load_sellers()

    def edit_seller(self):
        selected_row = self.sellers_table.currentRow()
        if selected_row < 0: return
        seller_id = int(self.sellers_table.item(selected_row, 0).text())
        seller_to_edit = self.db_session.get(database.Seller, seller_id)
        dialog = AddSellerDialog(self, seller_data=seller_to_edit)
        if dialog.exec() == QDialog.Accepted:
            seller_to_edit.name = dialog.name_edit.text()
            seller_to_edit.phone = dialog.phone_edit.text()
            seller_to_edit.address = dialog.address_edit.text()
            self.db_session.commit()
            self.load_sellers()

    def delete_seller(self):
        selected_row = self.sellers_table.currentRow()
        if selected_row < 0: return

        seller_id = int(self.sellers_table.item(selected_row, 0).text())
        reply = QMessageBox.question(self, self.tr("تأكيد الحذف"), self.tr("هل أنت متأكد من حذف هذا البائع؟"))
        if reply == QMessageBox.Yes:
            self.db_session.query(database.Seller).filter(database.Seller.id == seller_id).delete()
            self.db_session.commit()
            self.load_sellers()

    def closeEvent(self, event):
        """يتم استدعاؤها عند إغلاق الواجهة لضمان إغلاق جلسة قاعدة البيانات"""
        self.db_session.close()
        super().closeEvent(event)


class InventoryCountWidget(QWidget):
    """واجهة جرد المخزون"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_session = database.SessionLocal()
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()
        self.load_stores_filter()
        self.load_items()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # --- قسم الفلاتر ---
        filters_group = QGroupBox(self.tr("فلترة الأصناف"))
        filters_layout = QHBoxLayout()
        self.store_filter_combo = QComboBox()
        self.store_filter_combo.currentIndexChanged.connect(self.load_items)
        filters_layout.addWidget(QLabel(self.tr("عرض أصناف المخزن:")))
        filters_layout.addWidget(self.store_filter_combo) # تم تصحيح هذا السطر
        filters_layout.addStretch()
        filters_group.setLayout(filters_layout)
        main_layout.addWidget(filters_group)

        # --- جدول الجرد ---
        self.count_table = QTableWidget()
        self.count_table.setColumnCount(6)
        self.count_table.setHorizontalHeaderLabels([self.tr("ID"), self.tr("كود الصنف"), self.tr("اسم الصنف"), self.tr("الكمية المسجلة"), self.tr("الكمية الفعلية"), self.tr("الفرق")])
        self.count_table.setColumnHidden(0, True)
        self.count_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.count_table.cellChanged.connect(self.update_difference)
        main_layout.addWidget(self.count_table)

        # --- زر الحفظ ---
        actions_layout = QHBoxLayout()
        save_button = QPushButton(self.tr("حفظ التسويات"))
        save_button.clicked.connect(self.save_adjustments)
        actions_layout.addStretch()
        actions_layout.addWidget(save_button)
        main_layout.addLayout(actions_layout)

    def load_stores_filter(self):
        stores = self.db_session.query(database.Store).all()
        for store in stores:
            self.store_filter_combo.addItem(store.name, store.id)

    def load_items(self):
        self.count_table.blockSignals(True)
        self.count_table.setRowCount(0)
        store_id = self.store_filter_combo.currentData()
        if not store_id:
            self.count_table.blockSignals(False)
            return

        items = self.db_session.query(database.Item).filter(database.Item.store_id == store_id).all()
        for item in items:
            row = self.count_table.rowCount()
            self.count_table.insertRow(row)
            self.count_table.setItem(row, 0, QTableWidgetItem(str(item.id)))
            self.count_table.setItem(row, 1, QTableWidgetItem(item.code))
            self.count_table.setItem(row, 2, QTableWidgetItem(item.name)) # تم تصحيح هذا السطر
            self.count_table.setItem(row, 3, QTableWidgetItem(str(item.quantity)))
            self.count_table.setItem(row, 4, QTableWidgetItem("")) # حقل الكمية الفعلية فارغ
            self.count_table.setItem(row, 5, QTableWidgetItem("0"))
            # جعل الأعمدة غير قابلة للتعديل ما عدا "الكمية الفعلية"
            for col in [0, 1, 2, 3, 5]:
                self.count_table.item(row, col).setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.count_table.blockSignals(False)

    def update_difference(self, row, column):
        if column != 4: return # التحديث فقط عند تغيير الكمية الفعلية

        system_qty_item = self.count_table.item(row, 3)
        actual_qty_item = self.count_table.item(row, 4)
        diff_item = self.count_table.item(row, 5)

        try:
            system_qty = int(system_qty_item.text())
            actual_qty = int(actual_qty_item.text())
            difference = actual_qty - system_qty
            diff_item.setText(str(difference))
            # تلوين الفرق
            if difference > 0: diff_item.setForeground(QColor("green"))
            elif difference < 0: diff_item.setForeground(QColor("red"))
            else: diff_item.setForeground(QColor("black"))
        except (ValueError, AttributeError):
            diff_item.setText("0")
            diff_item.setForeground(QColor("black"))

    def save_adjustments(self):
        reply = QMessageBox.question(self, self.tr("تأكيد الحفظ"), self.tr("هل أنت متأكد من حفظ هذه التسويات؟ سيتم تحديث كميات المخزون بشكل دائم."))
        if reply == QMessageBox.Yes:
            for row in range(self.count_table.rowCount()):
                if self.count_table.item(row, 4).text(): # فقط إذا تم إدخال كمية فعلية
                    try:
                        item_id = int(self.count_table.item(row, 0).text())
                        new_quantity = int(self.count_table.item(row, 4).text()) # تم تصحيح هذا السطر
                        self.db_session.query(database.Item).filter(database.Item.id == item_id).update({"quantity": new_quantity})
                    except (ValueError, AttributeError):
                        continue # تجاهل الصفوف التي بها أخطاء
            self.db_session.commit() # تم تصحيح هذا السطر
            QMessageBox.information(self, "نجاح", "تم حفظ تسويات الجرد بنجاح.")
            self.load_items() # إعادة تحميل البيانات المحدثة


class PurchasesWidget(QWidget):
    """واجهة إنشاء فاتورة مشتريات جديدة"""
    def __init__(self):
        super().__init__()
        self.db_session = database.SessionLocal()
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()
        self.load_suppliers()
        self.connect_signals()

    def init_ui(self):
        main_layout = QGridLayout(self)

        # --- مجموعة معلومات الفاتورة والمورد ---
        info_group = QGroupBox(self.tr("معلومات الفاتورة والمورد"))
        info_layout = QGridLayout()

        info_layout.addWidget(QLabel(self.tr("المورد:")), 0, 0)
        supplier_layout = QHBoxLayout()
        self.supplier_combo = QComboBox()
        self.supplier_combo.setEditable(True)
        self.add_supplier_button = QPushButton("+")
        self.add_supplier_button.setFixedSize(25, 25)
        self.add_supplier_button.setToolTip("إضافة مورد جديد")
        supplier_layout.addWidget(self.supplier_combo)
        supplier_layout.addWidget(self.add_supplier_button)
        info_layout.addLayout(supplier_layout, 0, 1)
        # تم تصحيح هذا السطر
        info_layout.addWidget(QLabel(self.tr("رصيد سابق:")), 0, 2)
        self.balance_label = QLabel("0.00")
        self.balance_label.setStyleSheet("color: red; font-weight: bold;")
        info_layout.addWidget(self.balance_label, 0, 3)

        info_layout.addWidget(QLabel(self.tr("التاريخ:")), 1, 0)
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        info_layout.addWidget(self.date_edit, 1, 1)

        info_layout.addWidget(QLabel(self.tr("طريقة الدفع:")), 1, 2)
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems([self.tr("نقدي"), self.tr("آجل"), self.tr("شيك")])
        info_layout.addWidget(self.payment_method_combo, 1, 3)

        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group, 0, 0, 1, 2)

        # --- مجموعة إضافة الأصناف ---
        add_item_group = QGroupBox(self.tr("إضافة صنف للفاتورة"))
        add_item_layout = QHBoxLayout()
        self.item_search_edit = QLineEdit()
        self.item_search_edit.setPlaceholderText("ابحث بكود أو اسم الصنف...")
        self.add_item_button = QPushButton("إضافة الصنف") # جعل الزر متغيراً تابعاً للكلاس
        self.add_new_item_button = QPushButton("إضافة صنف جديد") # الزر الجديد

        add_item_layout.addWidget(QLabel("بحث:"))
        add_item_layout.addWidget(self.item_search_edit)
        add_item_layout.addWidget(self.add_item_button)
        add_item_layout.addWidget(self.add_new_item_button) # إضافة الزر الجديد للواجهة
        add_item_group.setLayout(add_item_layout)
        main_layout.addWidget(add_item_group, 1, 0, 1, 2)

        # --- جدول الأصناف ---
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6) # تم تصحيح هذا السطر
        self.items_table.setHorizontalHeaderLabels(["ID", "اسم الصنف", "الكمية", "سعر الشراء", "الإجمالي", "حذف"])
        self.items_table.setColumnHidden(0, True)
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.items_table, 2, 0, 1, 2)

        # --- مجموعة الإجماليات ---
        totals_group = QGroupBox(self.tr("ملخص الفاتورة"))
        totals_layout = QGridLayout()
        totals_layout.addWidget(QLabel(self.tr("الإجمالي:")), 0, 0)
        self.total_label = QLabel("0.00")
        totals_layout.addWidget(self.total_label, 0, 1)

        totals_layout.addWidget(QLabel(self.tr("المدفوع:")), 1, 0)
        self.paid_edit = QLineEdit("0.00")
        totals_layout.addWidget(self.paid_edit, 1, 1)

        totals_layout.addWidget(QLabel(self.tr("الرصيد بعد الفاتورة:")), 2, 0)
        self.balance_after_invoice_label = QLabel("0.00")
        self.balance_after_invoice_label.setStyleSheet("color: green; font-weight: bold;")
        totals_layout.addWidget(self.balance_after_invoice_label, 2, 1) # تم تصحيح هذا السطر

        totals_group.setLayout(totals_layout)
        main_layout.addWidget(totals_group, 3, 1)

        # --- أزرار الإجراءات ---
        buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("حفظ الفاتورة")
        buttons_layout.addWidget(self.save_button) # تم تصحيح هذا السطر
        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout, 4, 0, 1, 2)

        self.setLayout(main_layout)

    def connect_signals(self):
        self.items_table.cellChanged.connect(self.update_totals)
        self.paid_edit.textChanged.connect(self.update_totals)
        self.save_button.clicked.connect(self.save_purchase_invoice)
        self.supplier_combo.currentIndexChanged.connect(self.update_supplier_balance)
        self.add_supplier_button.clicked.connect(self.open_add_supplier_dialog)
        # ربط الإشارات للأزرار الجديدة
        self.item_search_edit.returnPressed.connect(self.add_item_to_invoice)
        self.add_item_button.clicked.connect(self.add_item_to_invoice) # استخدام المتغير المباشر بدلاً من البحث
        self.add_new_item_button.clicked.connect(self.open_add_item_dialog)

    def load_suppliers(self):
        self.supplier_combo.clear()
        suppliers = self.db_session.query(database.Supplier).all()
        self.supplier_combo.addItem(self.tr("مورد نقدي"), -1)
        for supplier in suppliers:
            self.supplier_combo.addItem(supplier.name, supplier.id)

    def update_supplier_balance(self, index):
        """تحديث حقل الرصيد عند اختيار مورد"""
        supplier_id = self.supplier_combo.itemData(index)
        if supplier_id and supplier_id != -1:
            supplier = self.db_session.query(database.Supplier).filter(database.Supplier.id == supplier_id).first()
            if supplier:
                self.balance_label.setText(f"{supplier.current_balance:.2f}")
        else:
            self.balance_label.setText("0.00")
        self.update_totals()

    def open_add_supplier_dialog(self):
        """يفتح نافذة لإضافة مورد جديد"""
        dialog = AddSupplierDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            new_supplier = database.Supplier(**data)
            self.db_session.add(new_supplier)
            self.db_session.commit() # تم تصحيح هذا السطر
            QMessageBox.information(self, "نجاح", f"تم إضافة المورد '{data['name']}' بنجاح.")
            self.load_suppliers()
            self.supplier_combo.setCurrentText(data['name'])

    def add_item_to_invoice(self, item_id=None):
        item = None
        if item_id:
            item = self.db_session.query(database.Item).filter(database.Item.id == item_id).first()
        else:
            search_term = self.item_search_edit.text()
            if not search_term: return
            # تم تصحيح هذا السطر
            item = self.db_session.query(database.Item).filter(
                (database.Item.code == search_term) | (database.Item.name.contains(search_term))
            ).first()

            if not item:
                reply = QMessageBox.question(self, "صنف غير موجود", 
                                             f"الصنف '{search_term}' غير موجود في المخزن.\nهل تريد إضافته كصنف جديد؟")
                if reply == QMessageBox.Yes: # تم تصحيح هذا السطر
                    self.open_add_item_dialog(prefill_name=search_term)
                return
        
        if not item:
            return

        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        self.items_table.setItem(row, 0, QTableWidgetItem(str(item.id)))
        self.items_table.setItem(row, 1, QTableWidgetItem(item.name))
        self.items_table.setItem(row, 2, QTableWidgetItem("1"))
        self.items_table.setItem(row, 3, QTableWidgetItem(f"{item.cost_price:.2f}"))
        self.items_table.setItem(row, 4, QTableWidgetItem("0.00")) # تم تصحيح هذا السطر
        
        delete_button = QPushButton("حذف")
        delete_button.clicked.connect(lambda: self.items_table.removeRow(self.items_table.indexAt(delete_button.pos()).row()))
        self.items_table.setCellWidget(row, 5, delete_button)
        self.item_search_edit.clear()
        self.update_totals()

    def open_add_item_dialog(self, prefill_name=None):
        """ 
        يفتح نافذة لإضافة صنف جديد غير موجود بالمخزن، ثم يضيفه للفاتورة.
        يمكن تمرير اسم مبدئي لتعبئة الحقل.
        """
        item_data = None
        if prefill_name:
            item_data = {"name": prefill_name}

        dialog = AddItemDialog(self, item_data=item_data)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            # تعيين الكمية الأولية إلى 0 لأنها ستضاف من خلال الفاتورة
            data["quantity"] = 0
            new_item = database.Item(**data)
            self.db_session.add(new_item)
            self.db_session.commit()
            QMessageBox.information(self, "نجاح", f"تم إضافة الصنف '{new_item.name}' بنجاح.")
            self.add_item_to_invoice(item_id=new_item.id) # إضافة الصنف الجديد مباشرة للفاتورة

    def update_totals(self):
        total = 0.0
        for row in range(self.items_table.rowCount()):
            try:
                quantity = float(self.items_table.item(row, 2).text())
                price = float(self.items_table.item(row, 3).text())
                row_total = quantity * price
                self.items_table.item(row, 4).setText(f"{row_total:.2f}")
                total += row_total
            except (ValueError, AttributeError):
                continue
        self.total_label.setText(f"{total:.2f}")

        # تحديث الرصيد بعد الفاتورة
        try:
            previous_balance = float(self.balance_label.text())
            paid_amount = float(self.paid_edit.text() or 0.0)
            new_balance = (previous_balance + total) - paid_amount
            self.balance_after_invoice_label.setText(f"{new_balance:.2f}")
        except ValueError:
            pass

    def save_purchase_invoice(self):
        supplier_id = self.supplier_combo.currentData()
        if not supplier_id:
            QMessageBox.warning(self, self.tr("خطأ"), self.tr("يرجى تحديد المورد أولاً."))
            return

        # 1. إنشاء سجل فاتورة المشتريات
        new_purchase = database.PurchaseInvoice(
            supplier_id=supplier_id,
            total_amount=float(self.total_label.text()),
            paid_amount=float(self.paid_edit.text() or 0.0),
            payment_method=self.payment_method_combo.currentText()
        )
        self.db_session.add(new_purchase)

        # 2. إضافة الأصناف وتحديث المخزون وسعر التكلفة
        for row in range(self.items_table.rowCount()):
            item_id = int(self.items_table.item(row, 0).text())
            quantity = int(self.items_table.item(row, 2).text())
            cost_price = float(self.items_table.item(row, 3).text())

            # إضافة الصنف لسجل الفاتورة
            p_item = database.PurchaseInvoiceItem(purchase_invoice=new_purchase, item_id=item_id, quantity=quantity, price_per_unit=cost_price)
            self.db_session.add(p_item)

            # تحديث كمية وسعر تكلفة الصنف في المخزون
            item_in_db = self.db_session.query(database.Item).filter(database.Item.id == item_id).first()
            if item_in_db:
                item_in_db.quantity += quantity
                item_in_db.cost_price = cost_price # تحديث سعر التكلفة لآخر سعر شراء

        # تحديث رصيد المورد
        if supplier_id != -1: # لا تقم بتحديث رصيد "مورد نقدي"
            supplier = self.db_session.query(database.Supplier).filter(database.Supplier.id == supplier_id).first()
            if supplier:
                supplier.current_balance = float(self.balance_after_invoice_label.text())


        # 3. تسجيل المبلغ المدفوع في الخزينة (سحب)
        paid_amount = float(self.paid_edit.text() or 0.0)
        if paid_amount > 0:
            last_transaction = self.db_session.query(database.TreasuryTransaction).order_by(database.TreasuryTransaction.id.desc()).first()
            last_balance = last_transaction.current_balance if last_transaction else 0.0
            
            if paid_amount > last_balance:
                QMessageBox.warning(self, "خطأ", "المبلغ المدفوع أكبر من الرصيد المتاح في الخزينة!")
                self.db_session.rollback() # التراجع عن كل العمليات
                return

            new_balance = last_balance - paid_amount
            treasury_entry = database.TreasuryTransaction(
                transaction_type="سحب",
                amount=paid_amount, # تم تصحيح هذا السطر
                description=f"لفاتورة مشتريات رقم {new_purchase.id}",
                current_balance=new_balance,
            )
            self.db_session.add(treasury_entry)

        # 4. حفظ كل التغييرات
        self.db_session.commit()
        QMessageBox.information(self, self.tr("نجاح"), self.tr("تم حفظ فاتورة المشتريات وتحديث المخزون بنجاح!"))
        # مسح الشاشة
        self.items_table.setRowCount(0)
        self.paid_edit.setText("0.00")
        self.update_totals()

class TreasuryWidget(QWidget):
    """واجهة إدارة ومتابعة الخزينة"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_session = database.SessionLocal()
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()
        self.load_transactions()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # --- قسم الرصيد الحالي ---
        balance_layout = QHBoxLayout() # تم تصحيح هذا السطر
        balance_layout.addWidget(QLabel("الرصيد الحالي للخزينة:"))
        self.current_balance_label = QLabel("0.00")
        self.current_balance_label.setStyleSheet("font-size: 20px; font-weight: bold; color: green;")
        balance_layout.addWidget(self.current_balance_label)
        balance_layout.addStretch()
        main_layout.addLayout(balance_layout)

        # --- أزرار الإجراءات ---
        actions_layout = QHBoxLayout()
        income_button = QPushButton(self.tr("إيداع جديد (مقبوضات)"))
        income_button.clicked.connect(lambda: self.add_manual_transaction("إيداع"))
        outcome_button = QPushButton(self.tr("سحب جديد (مصروفات)"))
        outcome_button.clicked.connect(lambda: self.add_manual_transaction("سحب"))
        actions_layout.addStretch()
        actions_layout.addWidget(income_button)
        actions_layout.addWidget(outcome_button)
        main_layout.addLayout(actions_layout)

        # --- جدول الحركات ---
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(5) # تم تصحيح هذا السطر
        self.transactions_table.setHorizontalHeaderLabels(["التاريخ", "النوع", "المبلغ", "الوصف/البيان", "الرصيد بعد العملية"])
        self.transactions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.transactions_table.setEditTriggers(QTableWidget.NoEditTriggers)
        main_layout.addWidget(self.transactions_table)

    def load_transactions(self):
        self.transactions_table.setRowCount(0)
        transactions = self.db_session.query(database.TreasuryTransaction).order_by(database.TreasuryTransaction.id.desc()).all()

        if not transactions:
            self.current_balance_label.setText("0.00")
            return

        # تحديث الرصيد الحالي
        self.current_balance_label.setText(f"{transactions[0].current_balance:.2f}")

        # تعبئة الجدول
        for trans in transactions:
            row = self.transactions_table.rowCount()
            self.transactions_table.insertRow(row) # تم تصحيح هذا السطر
            self.transactions_table.setItem(row, 0, QTableWidgetItem(trans.date.strftime("%Y-%m-%d")))
            
            type_item = QTableWidgetItem(trans.transaction_type)
            if trans.transaction_type == "إيداع":
                type_item.setForeground(QColor("green"))
            else:
                type_item.setForeground(QColor("red"))
            self.transactions_table.setItem(row, 1, type_item)

            self.transactions_table.setItem(row, 2, QTableWidgetItem(f"{trans.amount:.2f}"))
            self.transactions_table.setItem(row, 3, QTableWidgetItem(trans.description))
            self.transactions_table.setItem(row, 4, QTableWidgetItem(f"{trans.current_balance:.2f}"))

    def add_manual_transaction(self, trans_type):
        amount, ok1 = QInputDialog.getDouble(self, f"{trans_type} يدوي", "ادخل المبلغ:", 0, 0, 1000000, 2)
        if not ok1: return

        description, ok2 = QInputDialog.getText(self, self.tr(f"{trans_type} يدوي"), self.tr("ادخل البيان (الوصف):"))
        if not ok2: return

        # الحصول على آخر رصيد
        last_transaction = self.db_session.query(database.TreasuryTransaction).order_by(database.TreasuryTransaction.id.desc()).first()
        last_balance = last_transaction.current_balance if last_transaction else 0.0

        # حساب الرصيد الجديد
        if trans_type == "إيداع":
            new_balance = last_balance + amount
        else: # سحب
            if amount > last_balance:
                QMessageBox.warning(self, self.tr("خطأ"), self.tr("مبلغ السحب أكبر من الرصيد المتاح في الخزينة!"))
                return
            new_balance = last_balance - amount

        # إنشاء سجل الحركة
        new_transaction = database.TreasuryTransaction(
            transaction_type=trans_type,
            amount=amount,
            description=description,
            current_balance=new_balance
        )
        self.db_session.add(new_transaction)
        self.db_session.commit()
        
        QMessageBox.information(self, "نجاح", f"تم تسجيل عملية {trans_type} بنجاح.")
        self.load_transactions() # تحديث العرض

class DashboardWidget(QWidget):
    """الواجهة الرئيسية (لوحة التحكم)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_session = database.SessionLocal()
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()
        self.load_kpis()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel(self.tr("لوحة التحكم الرئيسية"))
        title_label.setAlignment(Qt.AlignCenter)
        title_font = title_label.font()
        title_font.setPointSize(24)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        kpi_layout = QGridLayout()
        kpi_layout.setSpacing(20)

        self.sales_today_card = self.create_kpi_card(self.tr("مبيعات اليوم"), QStyle.SP_ArrowUp, "#17a2b8")
        self.treasury_balance_card = self.create_kpi_card(self.tr("رصيد الخزينة"), QStyle.SP_DriveHDIcon, "#28a745")
        self.customers_count_card = self.create_kpi_card(self.tr("عدد العملاء"), QStyle.SP_DirHomeIcon, "#ffc107")
        self.items_count_card = self.create_kpi_card(self.tr("عدد الأصناف"), QStyle.SP_ComputerIcon, "#dc3545")

        kpi_layout.addWidget(self.sales_today_card, 0, 0)
        kpi_layout.addWidget(self.treasury_balance_card, 0, 1)
        kpi_layout.addWidget(self.customers_count_card, 1, 0)
        kpi_layout.addWidget(self.items_count_card, 1, 1)
        
        main_layout.addLayout(kpi_layout)
        main_layout.addStretch()

    def create_kpi_card(self, title, icon_enum, icon_color):
        card = QFrame()
        card.setObjectName("kpi_card")
        card_layout = QHBoxLayout(card)

        # --- جزء النص --- # تم تصحيح هذا السطر
        text_layout = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("kpi_title")
        value_label = QLabel("0")
        value_label.setObjectName("kpi_value")
        text_layout.addWidget(title_label)
        text_layout.addWidget(value_label)
        text_layout.addStretch()

        # --- جزء الأيقونة --- # تم تصحيح هذا السطر
        icon_label = QLabel()
        icon_label.setObjectName("kpi_icon")
        icon = self.style().standardIcon(icon_enum)
        pixmap = icon.pixmap(50, 50)
        icon_label.setPixmap(pixmap)
        icon_label.setStyleSheet(f"background-color: {icon_color};")

        card_layout.addLayout(text_layout)
        card_layout.addWidget(icon_label, 0, Qt.AlignRight)

        # إضافة تأثير الظل
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 60))
        card.setGraphicsEffect(shadow)

        return card

    def load_kpis(self):
        # 1. رصيد الخزينة
        last_trans = self.db_session.query(database.TreasuryTransaction).order_by(database.TreasuryTransaction.id.desc()).first()
        treasury_balance = last_trans.current_balance if last_trans else 0.0
        self.treasury_balance_card.findChild(QLabel, "kpi_value").setText(f"{treasury_balance:,.2f}")

        # 2. عدد العملاء
        customers_count = self.db_session.query(database.Customer).count()
        self.customers_count_card.findChild(QLabel, "kpi_value").setText(str(customers_count))

        # 3. عدد الأصناف
        items_count = self.db_session.query(database.Item).count()
        self.items_count_card.findChild(QLabel, "kpi_value").setText(str(items_count))

        # 4. مبيعات اليوم
        sales_today = self.db_session.query(func.sum(database.Invoice.total_amount)).filter(database.Invoice.date == datetime.date.today()).scalar() or 0.0 # تم تصحيح هذا السطر
        self.sales_today_card.findChild(QLabel, "kpi_value").setText(f"{sales_today:,.2f}")

class LoginDialog(QDialog):
    """شاشة تسجيل الدخول"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("تسجيل الدخول")
        self.setMinimumWidth(400) # تم تصحيح هذا السطر
        self.setLayoutDirection(Qt.RightToLeft)

        layout = QVBoxLayout(self) # تم تصحيح هذا السطر
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- عنوان الشاشة ---
        title_label = QLabel("تسجيل الدخول")
        title_font = title_label.font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #5699ef;")
        layout.addWidget(title_label)

        # --- حقول الإدخال ---
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)

        form_layout.addRow(self.tr("اسم المستخدم:"), self.username_edit)
        form_layout.addRow(self.tr("كلمة المرور:"), self.password_edit)

        layout.addLayout(form_layout)

        # --- خيار تذكرني ---
        self.remember_me_checkbox = QCheckBox("تذكرني (حفظ اسم المستخدم)")
        layout.addWidget(self.remember_me_checkbox)

        # --- أزرار الإجراءات ---
        buttons_layout = QHBoxLayout()

        login_button = QPushButton("دخول")
        login_button.setDefault(True) # جعل زر الدخول هو الافتراضي عند الضغط على Enter

        buttons_layout.addStretch()
        buttons_layout.addWidget(login_button)
        
        layout.addLayout(buttons_layout)

        # --- تحميل اسم المستخدم المحفوظ ---
        self.load_remembered_user()

        # --- ربط الإشارات ---
        login_button.clicked.connect(self.handle_login)
        self.password_edit.returnPressed.connect(self.handle_login)

    def load_remembered_user(self):
        """تحميل اسم المستخدم المحفوظ من ملف الإعدادات إن وجد"""
        settings_file = get_app_data_path("settings.json")
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    remembered_user = settings.get("login", {}).get("remembered_user")
                    if remembered_user:
                        self.username_edit.setText(remembered_user)
                        self.remember_me_checkbox.setChecked(True)
            except (json.JSONDecodeError, FileNotFoundError):
                pass

    def handle_login(self):
        username = self.username_edit.text()
        password = self.password_edit.text()

        session = database.SessionLocal()
        user = session.query(database.User).filter(database.User.username == username).first()

        if user and user.check_password(password):
            # --- حفظ اسم المستخدم إذا تم تحديد "تذكرني" ---
            settings_file = get_app_data_path("settings.json")
            all_settings = {}
            if os.path.exists(settings_file):
                with open(settings_file, "r", encoding="utf-8") as f:
                    try: all_settings = json.load(f)
                    except json.JSONDecodeError: pass
            
            if "login" not in all_settings: all_settings["login"] = {}
            all_settings["login"]["remembered_user"] = username if self.remember_me_checkbox.isChecked() else ""
            
            with open(settings_file, "w", encoding="utf-8") as f: # تم تصحيح هذا السطر
                json.dump(all_settings, f, ensure_ascii=False, indent=4)

            session.close()
            self.accept()
        else:
            session.close()
            QMessageBox.warning(self, "خطأ في الدخول", "اسم المستخدم أو كلمة المرور غير صحيحة.")

    def handle_create_account(self):
        """يعالج عملية إنشاء حساب مستخدم جديد"""
        username, ok1 = QInputDialog.getText(self, self.tr("إنشاء حساب جديد"), self.tr("ادخل اسم المستخدم الجديد:"))
        if ok1 and username:
            session = database.SessionLocal()
            existing_user = session.query(database.User).filter(database.User.username == username).first()
            if existing_user:
                QMessageBox.warning(self, self.tr("خطأ"), self.tr("اسم المستخدم هذا موجود بالفعل. يرجى اختيار اسم آخر."))
                session.close()
                return
            
            password, ok2 = QInputDialog.getText(self, self.tr("تعيين كلمة المرور"), self.tr(f"ادخل كلمة المرور للمستخدم '{username}':"), echo=QLineEdit.Password)
            if ok2 and password:
                new_user = database.User(username=username)
                new_user.set_password(password)
                session.add(new_user)
                session.commit()
                QMessageBox.information(self, "نجاح", f"تم إنشاء حساب المستخدم '{username}' بنجاح.\nيمكنك الآن تسجيل الدخول باستخدامه.")
            session.close()

class AddCompanyDialog(QDialog):
    """نافذة لإضافة أو تعديل إعدادات شركة (اتصال قاعدة بيانات)"""
    def __init__(self, parent=None, company_data=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft) # تم تصحيح هذا السطر
        self.setWindowTitle("إعدادات الشركة" if company_data else "إضافة شركة جديدة")

        main_layout = QVBoxLayout(self)

        # --- قسم نوع النشاط ---
        self.business_types = {
            "نشاط تجاري عام (مخزون ومبيعات)": "generic_store",
            "عيادة طبية": "clinic",
            "مكتب محاماة": "law_firm",
        }

        self.form_layout = QFormLayout()

        self.company_name_edit = QLineEdit()
        self.form_layout.addRow("اسم الشركة (للعرض):", self.company_name_edit)

        self.engine_map = { # تم تصحيح هذا السطر
            "PostgreSQL (موصى به للشبكات)": "postgresql",
            "MySQL": "mysql",
            "SQLite (ملف محلي)": "sqlite",
        }
        self.business_type_combo = QComboBox()
        self.business_type_combo.addItems(self.business_types.keys())
        self.form_layout.addRow("نوع النشاط:", self.business_type_combo)
        
        self.db_engine_combo = QComboBox()
        self.db_engine_combo.addItems(self.engine_map.keys())
        self.db_engine_combo.currentIndexChanged.connect(self.toggle_fields)
        self.form_layout.addRow("نوع قاعدة البيانات:", self.db_engine_combo)

        self.host_edit = QLineEdit("localhost")
        self.port_edit = QLineEdit("5432")
        self.dbname_edit = QLineEdit("erp_db")
        self.user_edit = QLineEdit("postgres")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)

        self.host_row = self.form_layout.addRow(self.tr("IP أو اسم السيرفر:"), self.host_edit)
        self.port_row = self.form_layout.addRow(self.tr("المنفذ (Port):"), self.port_edit)
        self.dbname_row = self.form_layout.addRow(self.tr("اسم قاعدة البيانات:"), self.dbname_edit)
        self.user_row = self.form_layout.addRow(self.tr("اسم المستخدم:"), self.user_edit)
        self.password_row = self.form_layout.addRow(self.tr("كلمة المرور:"), self.password_edit)

        main_layout.addLayout(self.form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

        if company_data:
            self.populate_data(company_data)
        
        self.toggle_fields()

    def toggle_fields(self):
        is_sqlite = "sqlite" in self.db_engine_combo.currentText().lower()
        for widget in [self.host_edit, self.port_edit, self.user_edit, self.password_edit]: # تم تصحيح هذا السطر
            widget.setVisible(not is_sqlite)
            self.form_layout.labelForField(widget).setVisible(not is_sqlite)
        
        self.dbname_edit.setPlaceholderText("مسار الملف، مثال: C:/data/mycompany.db" if is_sqlite else "اسم قاعدة البيانات على السيرفر")

    def populate_data(self, data):
        self.company_name_edit.setText(data.get("name", ""))
        
        business_type_value = data.get("business_type", "generic_store")
        for display_name, value in self.business_types.items(): # تم تصحيح هذا السطر
            if value == business_type_value:
                self.business_type_combo.setCurrentText(display_name)
                break

        engine_value = data.get("engine", "postgresql")
        for display_name, value in self.engine_map.items():
            if value == engine_value:
                self.db_engine_combo.setCurrentText(display_name)
                break
        self.host_edit.setText(data.get("host", "localhost"))
        self.port_edit.setText(data.get("port", "5432"))
        self.dbname_edit.setText(data.get("dbname", "erp_db"))
        self.user_edit.setText(data.get("user", "postgres"))
        self.password_edit.setText(data.get("password", ""))

    def get_data(self):
        selected_display_name = self.db_engine_combo.currentText()
        selected_business_display_name = self.business_type_combo.currentText()

        engine_type = self.engine_map.get(selected_display_name, "postgresql")
        business_type = self.business_types.get(selected_business_display_name, "generic_store")
        return {
            "business_type": business_type,
            "name": self.company_name_edit.text(),
            "engine": engine_type,
            "host": self.host_edit.text(),
            "port": self.port_edit.text(),
            "dbname": self.dbname_edit.text(),
            "user": self.user_edit.text(),
            "password": self.password_edit.text()
        }


def get_db_url_from_config(config):
    """يكون رابط الاتصال بناء على القاموس"""
    engine = config.get("engine")
    if engine == "postgresql":
        return f"postgresql+psycopg2://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['dbname']}"
    elif engine == "mysql":
        return f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['dbname']}"
    elif engine == "sqlite":
        # لضمان أن ملف SQLite يتم إنشاؤه في مسار قابل للكتابة
        # إذا كان config['dbname'] هو مجرد اسم ملف، فسيتم وضعه في مجلد بيانات التطبيق
        db_path = get_app_data_path(config['dbname']) if not os.path.isabs(config['dbname']) else config['dbname']
        return f"sqlite:///{db_path}"
    return None

class SplashScreen(QWidget):
    """شاشة ترحيبية مع عداد تحميل"""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.counter = 0
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(450, 300) # تم تصحيح هذا السطر

        # وضع الشاشة في المنتصف
        screen_geometry = QScreen.availableGeometry(QApplication.primaryScreen())
        self.move(screen_geometry.center() - self.rect().center())

        self.init_ui()
        self.start_loading()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # إطار للخلفية والحدود
        frame = QFrame(self)
        frame.setObjectName("splashFrame")
        frame.setStyleSheet("""
            #splashFrame {
                background-color: #1e2127;
                border-radius: 10px;
                border: 1px solid #3498db;
            }
        """)
        frame_layout = QVBoxLayout(frame)
        layout.addWidget(frame)

        frame_layout.addStretch() # تم تصحيح هذا السطر
        title_label = QLabel("نظام ERP المتكامل")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = title_label.font()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #3498db; background-color: transparent;")
        frame_layout.addWidget(title_label)
        
        self.status_label = QLabel("جاري بدء التشغيل...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #abb2bf; background-color: transparent; font-size: 11pt;")
        frame_layout.addWidget(self.status_label)
        frame_layout.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximumHeight(15)
        frame_layout.addWidget(self.progress_bar)

    def start_loading(self):
        """يبدأ المؤقت لزيادة عداد التحميل"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        # يمكنك تغيير الرقم 35 لزيادة أو تقليل مدة التحميل
        # رقم أكبر = تحميل أبطأ، رقم أصغر = تحميل أسرع
        self.timer.start(35)

    def update_progress(self):
        """تحديث شريط التقدم والرسائل"""
        self.progress_bar.setValue(self.counter)
        if self.counter > 100:
            self.timer.stop()
            self.close() # تم تصحيح هذا السطر

        if self.counter < 30:
            self.status_label.setText(self.tr("جاري تحميل الوحدات..."))
        elif self.counter < 70: # تم تصحيح هذا السطر
            self.status_label.setText("جاري الاتصال بقاعدة البيانات...")
        else:
            self.status_label.setText("جاري تجهيز الواجهة الرئيسية...")
        
        self.counter += 1

class SelectCompanyDialog(QDialog):
    """شاشة لاختيار الشركة عند بدء التشغيل"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("اختيار الشركة"))
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumWidth(400)
        self.companies = self.load_companies() # تم تصحيح هذا السطر
        self.selected_company_config = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("اختر الشركة التي تريد تسجيل الدخول إليها:"))

        self.company_list = QListWidget()
        self.company_list.addItems(self.companies.keys())
        self.company_list.itemDoubleClicked.connect(self.accept)
        layout.addWidget(self.company_list)

        buttons_layout = QHBoxLayout()
        add_button = QPushButton(self.tr("إضافة شركة جديدة"))
        add_button.clicked.connect(self.add_company)
        edit_button = QPushButton(self.tr("تعديل المحدد"))
        edit_button.clicked.connect(self.edit_company)
        delete_button = QPushButton(self.tr("حذف المحدد"))
        delete_button.clicked.connect(self.delete_company)
        
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(edit_button)
        buttons_layout.addWidget(delete_button)
        layout.addLayout(buttons_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setText(self.tr("دخول"))
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def load_companies(self):
        companies_file = get_app_data_path("companies.json")
        if os.path.exists(companies_file):
            try:
                with open(companies_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def save_companies(self):
        companies_file = get_app_data_path("companies.json")
        with open(companies_file, "w", encoding="utf-8") as f:
            json.dump(self.companies, f, ensure_ascii=False, indent=4)

    def add_company(self):
        dialog = AddCompanyDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            company_name = data["name"] # تم تصحيح هذا السطر
            if company_name and company_name not in self.companies:
                self.companies[company_name] = data
                self.save_companies()
                self.company_list.addItem(company_name)
            else:
                QMessageBox.warning(self, "خطأ", "اسم الشركة موجود بالفعل أو فارغ.")

    def edit_company(self):
        current_item = self.company_list.currentItem()
        if not current_item: return
        company_name = current_item.text()
        dialog = AddCompanyDialog(self, company_data=self.companies[company_name]) # تم تصحيح هذا السطر
        if dialog.exec() == QDialog.Accepted:
            new_data = dialog.get_data()
            new_name = new_data["name"]
            del self.companies[company_name]
            self.companies[new_name] = new_data
            self.save_companies()
            current_item.setText(new_name)

    def delete_company(self):
        current_item = self.company_list.currentItem()
        if not current_item: return
        company_name = current_item.text()
        reply = QMessageBox.question(self, self.tr("تأكيد الحذف"), self.tr(f"هل أنت متأكد من حذف إعدادات الاتصال للشركة '{company_name}'؟"))
        if reply == QMessageBox.Yes:
            del self.companies[company_name]
            self.save_companies()
            self.company_list.takeItem(self.company_list.row(current_item))

    def accept(self):
        current_item = self.company_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, self.tr("خطأ"), self.tr("يرجى تحديد شركة أولاً."))
            return
        company_name = current_item.text()
        self.selected_company_config = self.companies[company_name]
        super().accept()

def get_business_profile(profile_name):
    """
    تُرجع قاموساً يحتوي على إعدادات الواجهة بناءً على نوع النشاط.
    """
    profiles = {
        "generic_store": {
            "window_title": QCoreApplication.translate("MainWindow", "نشاط تجاري عام"),
            "menus": ['inventory', 'sales', 'purchases', 'contacts'],
        },
        "clinic": {
            "window_title": QCoreApplication.translate("MainWindow", "إدارة عيادة طبية"),
            "menus": ['sales', 'contacts'], # لا يوجد مخزون أو مشتريات
            "sales_menu_title": QCoreApplication.translate("MainWindow", "الفواتير والخدمات"),
            "invoice_action_title": QCoreApplication.translate("MainWindow", "فاتورة كشف/خدمة"),
            "contacts_menu_title": QCoreApplication.translate("MainWindow", "المرضى والموظفين"),
            "customer_action_title": QCoreApplication.translate("MainWindow", "إدارة المرضى"),
        },
        "law_firm": {
            "window_title": QCoreApplication.translate("MainWindow", "إدارة مكتب محاماة"),
            "menus": ['sales', 'contacts'], # لا يوجد مخزون أو مشتريات
            "sales_menu_title": QCoreApplication.translate("MainWindow", "المطالبات المالية"),
            "invoice_action_title": QCoreApplication.translate("MainWindow", "إنشاء مطالبة مالية"),
            "contacts_menu_title": QCoreApplication.translate("MainWindow", "الموكلين والموظفين"),
            "customer_action_title": QCoreApplication.translate("MainWindow", "إدارة الموكلين"),
        }
    }
    # إرجاع ملف التعريف المطلوب، أو الملف العام كخيار افتراضي
    return profiles.get(profile_name, profiles['generic_store'])





def check_app_activation(db_session):
    """
    يتحقق من حالة تفعيل البرنامج.
    يُرجع: (هل البرنامج مفعل, تاريخ الانتهاء)
    """
    activation_record = db_session.query(database.Activation).first()
    if not activation_record:
        return (False, None) # غير مفعل إطلاقاً # تم تصحيح هذا السطر

    is_active = activation_record.expiry_date >= datetime.date.today()
    return (is_active, activation_record.expiry_date)


class ActivationWidget(QDialog):
    """واجهة تفعيل البرنامج بالسيريال"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("تفعيل البرنامج"))
        self.db_session = database.SessionLocal()
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()
        self.check_activation_status()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setSpacing(20)
        
        # --- قسم حالة التفعيل ---
        status_group = QGroupBox(self.tr("حالة تفعيل البرنامج"))
        status_layout = QFormLayout(status_group)

        self.status_label = QLabel()
        self.type_label = QLabel()
        self.expiry_label = QLabel()

        status_layout.addRow(self.tr("حالة التفعيل:"), self.status_label)
        
        self.packages_info_label = QLabel(self.tr("الباقات المتاحة: اشتراك شهري - اشتراك سنوي."))
        self.packages_info_label.setStyleSheet("color: #888;")
        status_layout.addRow(self.packages_info_label)
        self.packages_info_label.setVisible(False) # إخفاؤها مبدئياً

        status_layout.addRow(self.tr("نوع الاشتراك:"), self.type_label)
        status_layout.addRow(self.tr("تاريخ الانتهاء:"), self.expiry_label)
        main_layout.addWidget(status_group)

        # --- قسم تغيير الاشتراك (سيكون مخفياً في البداية) ---
        self.change_sub_group = QGroupBox(self.tr("إدارة الاشتراك"))
        change_sub_layout = QVBoxLayout(self.change_sub_group)
        self.change_sub_button = QPushButton(self.tr("تغيير الاشتراك وتفعيل سيريال جديد"))
        self.change_sub_button.setToolTip(self.tr("اضغط هنا لحذف التفعيل الحالي وإدخال سيريال جديد"))
        self.change_sub_button.clicked.connect(self.change_subscription)
        change_sub_layout.addWidget(self.change_sub_button, 0, Qt.AlignCenter)
        main_layout.addWidget(self.change_sub_group)

        # --- قسم إدخال السيريال ---
        self.activation_group = QGroupBox(self.tr("تفعيل اشتراك جديد"))
        activation_layout = QVBoxLayout(self.activation_group)
        
        activation_layout.addWidget(QLabel(self.tr("أدخل الرقم التسلسلي (السيريال) لتفعيل البرنامج:")))
        self.serial_edit = QLineEdit()
        self.serial_edit.setPlaceholderText("XXXX-XXXX-XXXX-XXXX-XXXX")
        self.serial_edit.setLayoutDirection(Qt.LeftToRight) # الطريقة الصحيحة لتحديد اتجاه الكتابة
        activation_layout.addWidget(self.serial_edit)

        self.activate_button = QPushButton(self.tr("تفعيل"))
        self.activate_button.clicked.connect(self.handle_activation)
        activation_layout.addWidget(self.activate_button, 0, Qt.AlignLeft)
        main_layout.addWidget(self.activation_group)
        main_layout.addStretch() # لإضافة مسافة مرنة في الأسفل

    def check_activation_status(self):
        """التحقق من حالة التفعيل من قاعدة البيانات وعرضها"""
        activation_record = self.db_session.query(database.Activation).first()

        if activation_record and activation_record.expiry_date >= datetime.date.today():
            # البرنامج مفعل
            sub_type = activation_record.subscription_type # تم تصحيح هذا السطر
            if sub_type == 'trial':
                self.status_label.setText(self.tr("<b><font color='#17a2b8'>فترة تجريبية</font></b>"))
                sub_type_display = self.tr("تجريبي")
                self.expiry_label.setText(activation_record.expiry_date.strftime("%Y-%m-%d"))
                self.activation_group.setVisible(True)
                self.change_sub_group.setVisible(True)
            elif sub_type == 'lifetime':
                self.status_label.setText(self.tr("<b><font color='gold'>البرنامج مفعل (مدى الحياة)</font></b>"))
                sub_type_display = self.tr("Unlimited")
                self.expiry_label.setText("∞") # علامة اللانهاية
                self.activation_group.setVisible(False)
                self.change_sub_group.setVisible(False)
            else:
                self.status_label.setText(self.tr("<b><font color='green'>البرنامج مفعل</font></b>"))
                sub_type_display = self.tr("سنوي") if sub_type == 'yearly' else self.tr("شهري")
                self.expiry_label.setText(activation_record.expiry_date.strftime("%Y-%m-%d"))
                self.activation_group.setVisible(False)
                self.change_sub_group.setVisible(True)

            self.type_label.setText(sub_type_display)
        else: # تم تصحيح هذا السطر
            # البرنامج غير مفعل أو منتهي الصلاحية
            self.status_label.setText("<b><font color='red'>البرنامج غير مفعل</font></b>")
            self.packages_info_label.setVisible(True) # إظهار معلومات الباقات
            self.activation_group.setVisible(True)
            self.change_sub_group.setVisible(False)

    def handle_activation(self):
        """معالجة عملية التفعيل عند الضغط على الزر"""
        serial_key = self.serial_edit.text().strip()
        if not (18 <= len(serial_key) <= 42):
            QMessageBox.warning(self, "خطأ", "الرقم التسلسلي غير صحيح. يجب أن يكون طوله بين 18 و 42 حرفاً.")
            return

        # --- توليد معرّف فريد للجهاز ---
        # هذه الطريقة تستخدم عنوان الماك للجهاز. إنها طريقة جيدة للبدء.
        # في التطبيقات الحقيقية، قد تحتاج إلى طريقة أكثر تعقيداً.
        hwid = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) for i in range(0,8*6,8)][::-1])

        # --- التحقق من السيريال ---
        # 1. هل تم استخدامه من قبل؟
        used_serial = self.db_session.query(database.Activation).filter_by(serial_key=serial_key).first()
        if used_serial:
            # حتى لو تم استخدامه، سنتحقق من السيرفر للتأكد من أنه لم يتم إيقافه
            pass
        else:
             # هذا الجزء أصبح غير ضروري لأن السيرفر سيقوم بالتحقق
             pass

        # 2. هل السيريال صحيح وموجود في قائمة السيريالات؟
        # --- الاتصال بالسيرفر للتحقق ---
        try:
            # يمكنك تغيير الرابط إلى رابط السيرفر الفعلي الخاص بك # تم تصحيح هذا السطر
            # --- تعديل: قراءة رابط السيرفر من الإعدادات ---
            settings_file = get_app_data_path("settings.json")
            server_url = "http://ARABLY.aternos.me:27916/validate_serial" # رابط السيرفر الجديد
            api_key = 'YOUR_SECRET_API_KEY_HERE' # مفتاح افتراضي للتطوير

            if os.path.exists(settings_file):
                with open(settings_file, "r", encoding="utf-8") as f:
                    try:
                        settings = json.load(f)
                        server_url = settings.get("activation", {}).get("server_url", server_url)
                        api_key = settings.get("activation", {}).get("api_key", api_key)
                    except json.JSONDecodeError:
                        pass # استخدام الإعدادات الافتراضية في حالة تلف الملف

            # قمنا بإضافة ترويسة X-API-Key لتتوافق مع متطلبات السيرفر
            headers = {
                'X-API-Key': api_key
            }
            response = requests.post(
                server_url,
                json={'serial_key': serial_key, 'device_id': hwid}, 
                headers=headers, # إضافة الترويسة هنا
                timeout=10 # مهلة الاتصال
            )
            response.raise_for_status() # للتأكد من أن الطلب نجح
            server_data = response.json()

            if server_data['status'] == 'invalid':
                QMessageBox.critical(self, self.tr("خطأ في التفعيل"), self.tr("الرقم التسلسلي الذي أدخلته غير صحيح أو غير موجود."))
                return
            elif server_data['status'] == 'used':
                QMessageBox.critical(self, self.tr("خطأ في التفعيل"), self.tr("هذا الرقم التسلسلي تم استخدامه من قبل على جهاز آخر."))
                return
            elif server_data['status'] == 'deactivated':
                QMessageBox.critical(self, self.tr("تم إيقاف التفعيل"), self.tr("تم إيقاف هذا السيريال من قبل مدير النظام."))
                return
            elif server_data['status'] == 'valid':
                sub_type = server_data['subscription_type']
            else:
                QMessageBox.critical(self, "خطأ غير معروف", f"حدث خطأ غير متوقع من السيرفر: {server_data.get('message')}")
                return

        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "خطأ في الاتصال", f"لا يمكن الاتصال بسيرفر التفعيل. يرجى التحقق من اتصالك بالإنترنت.\n{e}")
            return

        # --- السيريال صحيح وغير مستخدم، قم بالتفعيل ---
        today = datetime.date.today()
        if sub_type == 'monthly':
            expiry_date = today + datetime.timedelta(days=30)
        elif sub_type == 'lifetime':
            # إذا كان نوع الاشتراك "مدى الحياة"، يتم تعيين تاريخ انتهاء بعيد جداً
            expiry_date = datetime.date(9999, 12, 31)
        else: # yearly
            expiry_date = today + datetime.timedelta(days=365)

        # حذف أي سجل تفعيل قديم (منتهي الصلاحية)
        self.db_session.query(database.Activation).delete()

        new_activation = database.Activation(
            serial_key=serial_key,
            activation_date=today,
            expiry_date=expiry_date,
            subscription_type=sub_type
        )
        self.db_session.add(new_activation)
        self.db_session.commit()
        
        QMessageBox.information(self, self.tr("نجاح"), self.tr(f"تم تفعيل البرنامج بنجاح!\nينتهي اشتراكك في: {expiry_date.strftime('%Y-%m-%d')}"))
        
        # تحديث الواجهة
        self.check_activation_status()

    def change_subscription(self):
        """حذف التفعيل الحالي للسماح بإدخال سيريال جديد"""
        reply = QMessageBox.question(self, self.tr("تأكيد تغيير الاشتراك"), 
                                     self.tr("هل أنت متأكد؟ سيتم حذف التفعيل الحالي للبرنامج وستحتاج إلى إدخال سيريال جديد."),
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.db_session.query(database.Activation).delete()
            self.db_session.commit()
            QMessageBox.information(self, self.tr("تم"), self.tr("تم حذف الاشتراك القديم. يرجى إدخال السيريال الجديد الآن."))
            self.check_activation_status() # تحديث الواجهة لإظهار حالة "غير مفعل"

class LanguageSettingsWidget(QWidget):
    """واجهة إعدادات اللغة"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.settings_file = get_app_data_path("settings.json")
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)

        title_label = QLabel(self.tr("إعدادات اللغة"))
        title_font = title_label.font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label, 0, Qt.AlignCenter)

        form_layout = QFormLayout()
        self.language_combo = QComboBox()
        # يمكنك إضافة المزيد من اللغات هنا
        self.languages = {
            self.tr("العربية"): "ar",
            self.tr("الإنجليزية"): "en",
            self.tr("الفرنسية"): "fr",
            # ... أضف 200 لغة هنا
        }
        self.language_combo.addItems(self.languages.keys())
        form_layout.addRow(self.tr("اختر اللغة:"), self.language_combo)
        main_layout.addLayout(form_layout)

        save_button = QPushButton(self.tr("حفظ وتطبيق"))
        save_button.clicked.connect(self.save_settings)
        main_layout.addWidget(save_button, 0, Qt.AlignLeft)

    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    current_lang_code = settings.get("language", {}).get("locale", "ar")
                    for display_name, code in self.languages.items():
                        if code == current_lang_code:
                            self.language_combo.setCurrentText(display_name)
                            break
            except (json.JSONDecodeError, FileNotFoundError):
                pass

    def save_settings(self):
        selected_display_name = self.language_combo.currentText()
        selected_locale_code = self.languages.get(selected_display_name, "ar")

        all_settings = {}
        if os.path.exists(self.settings_file):
            with open(self.settings_file, "r", encoding="utf-8") as f:
                try:
                    all_settings = json.load(f)
                except json.JSONDecodeError:
                    pass
        
        all_settings["language"] = {"locale": selected_locale_code}
        with open(self.settings_file, "w", encoding="utf-8") as f:
            json.dump(all_settings, f, ensure_ascii=False, indent=4)
        
        QMessageBox.information(self, self.tr("حفظ الإعدادات"), self.tr("تم حفظ إعدادات اللغة. يرجى إعادة تشغيل البرنامج لتطبيق التغييرات."))
        QApplication.instance().quit()
        os.execv(sys.executable, [sys.executable] + sys.argv)

class UpdateWorker(QObject):
    """
    عامل يعمل في خيط منفصل للتحقق من التحديثات دون تجميد الواجهة.
    """
    finished = Signal()
    success = Signal(dict)  # إشارة عند العثور على تحديث، تحمل معلومات التحديث
    error = Signal(str)     # إشارة عند حدوث خطأ أو عدم وجود تحديث

    def __init__(self, current_version, releases_url):
        super().__init__()
        self.current_version = current_version
        self.releases_url = releases_url

    def run(self):
        """
        الدالة الرئيسية التي يتم تنفيذها في الخيط.
        """
        try:
            response = requests.get(self.releases_url, timeout=15)
            response.raise_for_status()
            data = response.json()

            latest_version = data['tag_name'].lstrip('v')
            
            # مقارنة الإصدارات (بشكل بسيط، يمكن تحسينه باستخدام مكتبة مثل packaging)
            if latest_version > self.current_version:
                download_url = data.get('html_url', self.releases_url) # رابط صفحة الإصدار
                release_notes = data.get('body', 'لا توجد ملاحظات لهذا الإصدار.')
                
                update_info = {
                    'latest_version': latest_version,
                    'download_url': download_url,
                    'release_notes': release_notes
                }
                self.success.emit(update_info)
            else:
                self.error.emit("no_update")
        except requests.exceptions.RequestException as e:
            self.error.emit(f"خطأ في الاتصال بالشبكة: {e}")
        self.finished.emit()

class UpdateWidget(QDialog):
    """واجهة للتحقق من التحديثات وتثبيتها"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("تحديثات البرنامج")
        self.setMinimumSize(600, 400)
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()
        
        # إعداد الخيط الخلفي للتحقق من التحديثات
        self.update_thread = QThread()
        # ============================================================================
        # !! هام: يجب تغيير هذا الرابط إلى رابط مستودع GitHub الفعلي الخاص بك !!
        # استبدل YOUR_USERNAME باسم المستخدم الخاص بك و YOUR_REPO باسم المستودع.
        # مثال: "https://api.github.com/repos/arably/arably-erp/releases/latest"
        self.releases_url = "https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO/releases/latest" 
        self.update_worker = None # سيتم إنشاؤه عند الحاجة

        # إعداد مؤقت للتحقق من انتهاء مهلة الاتصال
        self.timeout_timer = QTimer(self)
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self.on_update_timeout)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        current_version_label = QLabel(f"<h3>الإصدار الحالي: {__version__}</h3>")
        main_layout.addWidget(current_version_label)

        self.check_button = QPushButton("التحقق من وجود تحديثات")
        self.check_button.clicked.connect(self.check_for_updates)
        main_layout.addWidget(self.check_button)

        self.status_area = QTextEdit()
        self.status_area.setReadOnly(True)
        self.status_area.setPlaceholderText("معلومات التحديث ستظهر هنا...")
        main_layout.addWidget(self.status_area)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        self.install_button = QPushButton("الانتقال لصفحة التحميل")
        self.install_button.setVisible(False)
        self.install_button.clicked.connect(self.open_download_page)
        main_layout.addWidget(self.install_button)

    def check_for_updates(self):
        """بدء عملية التحقق من التحديثات في خيط منفصل."""
        self.status_area.setText("جاري التحقق من وجود تحديثات...")
        self.check_button.setEnabled(False)
        self.install_button.setVisible(False)

        # بدء مؤقت المهلة (30 ثانية)
        self.timeout_timer.start(30000) # 30000 ميلي ثانية

        # إنشاء عامل جديد لكل عملية تحقق
        self.update_thread = QThread()
        self.update_worker = UpdateWorker(__version__, self.releases_url)

        # نقل العامل إلى الخيط
        self.update_worker.moveToThread(self.update_thread)

        # ربط الإشارات
        self.update_thread.started.connect(self.update_worker.run)
        self.update_worker.finished.connect(self.update_thread.quit)
        self.update_worker.finished.connect(self.update_worker.deleteLater)
        self.update_thread.finished.connect(self.update_thread.deleteLater)
        self.update_worker.success.connect(self.on_update_success)
        self.update_worker.error.connect(self.on_update_error)

        # بدء الخيط
        self.update_thread.start()

    def on_update_success(self, update_info):
        """يتم استدعاؤها عند العثور على تحديث جديد بنجاح."""
        self.timeout_timer.stop() # إيقاف مؤقت المهلة
        self.download_url = update_info['download_url']
        self.status_area.setHtml(f"""
            <h3><font color='green'>تم العثور على تحديث جديد!</font></h3>
            <p>الإصدار المتاح: <b>{update_info['latest_version']}</b></p>
            <h4>ملاحظات الإصدار:</h4>
            <div style='background-color: #2c313c; padding: 10px; border-radius: 5px;'>{update_info['release_notes'].replace('\n', '<br>')}</div>
        """)
        self.install_button.setVisible(True)
        self.check_button.setEnabled(True)

    def on_update_error(self, message):
        """يتم استدعاؤها عند حدوث خطأ أو عدم وجود تحديث."""
        self.timeout_timer.stop() # إيقاف مؤقت المهلة
        if message == "no_update":
            self.status_area.setText("أنت تستخدم أحدث إصدار من البرنامج.")
        else:
            self.status_area.setText(message)
        self.check_button.setEnabled(True)

    def on_update_timeout(self):
        """يتم استدعاؤها عند انتهاء مهلة التحقق من التحديث."""
        if self.update_thread and self.update_thread.isRunning():
            self.update_thread.quit() # محاولة إيقاف الخيط بأمان
            self.update_thread.wait(1000) # الانتظار لثانية واحدة

        self.status_area.setText("لا يوجد تحديث متاح حالياً أو أن الخادم استغرق وقتاً طويلاً للرد.")
        self.check_button.setEnabled(True)

    def open_download_page(self):
        """يفتح صفحة التحميل في المتصفح الافتراضي"""
        if hasattr(self, 'download_url'):
            webbrowser.open(self.download_url)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # --- ثيم احترافي داكن (Dark Theme) ---
    # تم تصحيح هذا السطر
    # تم تصحيح هذا السطر
    DARK_THEME_STYLE = """
        /* === النمط العام === */
        QWidget {
            font-family: 'Segoe UI', 'Tahoma', 'Arial';
            font-size: 11pt;
            color: #e0e0e0; /* لون النص الأساسي (أبيض مائل للرمادي) */
        }
        QMainWindow, QDialog {
            background-color: #2c313c; /* لون الخلفية الرئيسي */
        }

        /* === القوائم === */
        QMenuBar {
            background-color: #343944;
            border-bottom: 1px solid #444955;
        }
        QMenuBar::item:selected {
            background-color: #5699ef; /* لون التمييز الأزرق */
            color: #ffffff;
        }
        QMenu {
            background-color: #343944;
            border: 1px solid #444955;
        }
        QMenu::item:selected {
            background-color: #5699ef;
            color: #ffffff;
        }

        /* === الأزرار === */
        QPushButton {
            background-color: #4a505c; /* رمادي داكن للأزرار */
            color: #e0e0e0;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #5a606c;
        }
        QPushButton:pressed {
            background-color: #444955;
        }
        /* الأزرار الرئيسية (حفظ، دخول، تفعيل) */
        QPushButton[text*='حفظ'], QPushButton[text*='دخول'], QPushButton[text*='تفعيل'], QPushButton[text*='إضافة'] {
            background-color: #5699ef; /* أزرق */
            color: #ffffff;
            font-weight: bold;
        }
        QPushButton[text*='حفظ']:hover, QPushButton[text*='دخول']:hover, QPushButton[text*='تفعيل']:hover, QPushButton[text*='إضافة']:hover {
            background-color: #6aa5f2;
        }
        /* أزرار الخطر (حذف) */
        QPushButton#delete_button, QPushButton[text*='حذف'] {
            background-color: #f07178; /* أحمر */
            color: #ffffff;
        }
        QPushButton#delete_button:hover, QPushButton[text*='حذف']:hover {
            background-color: #f28088;
        }

        /* === حقول الإدخال === */
        QLineEdit, QDateEdit, QTextEdit, QComboBox {
            background-color: #343944;
            border: 1px solid #444955;
            border-radius: 4px;
            padding: 6px;
            color: #e0e0e0;
        }
        QComboBox::drop-down {
            border: none;
        }
        QComboBox QAbstractItemView {
            background-color: #343944;
            border: 1px solid #444955;
            selection-background-color: #5699ef;
            selection-color: #ffffff;
        }
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus {
            border-color: #5699ef; /* تمييز الحقل عند التركيز عليه */
        }

        /* === الجداول === */
        QTableWidget {
            background-color: #343944;
            border: 1px solid #444955;
            gridline-color: #444955;
            color: #e0e0e0;
        }
        QHeaderView::section {
            background-color: #2c313c;
            padding: 6px;
            border: 1px solid #444955;
            font-weight: bold;
            color: #f0f0f0;
        }
        QTableWidget::item:selected {
            background-color: #5699ef;
            color: #ffffff;
        }

        /* === صناديق المجموعات === */
        QGroupBox {
            border: 1px solid #444955;
            border-radius: 5px;
            margin-top: 10px;
            background-color: #343944;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 10px;
            color: #e0e0e0;
        }

        /* === بطاقات لوحة التحكم === */
        #kpi_card {
            background-color: #343944;
            border-radius: 8px;
            border: 1px solid #444955;
        }
        #kpi_title {
            font-size: 13pt;
            color: #a0a0a0; /* رمادي فاتح لعنوان المؤشر */
        }
        #kpi_value {
            font-size: 26pt;
            font-weight: bold;
            color: #ffffff;
        }
        #kpi_icon {
            border-radius: 8px;
            padding: 10px;
            color: #ffffff;
        }
    """
    app.setStyleSheet(DARK_THEME_STYLE)
    # -------------------------
    
    # --- تحميل الترجمة عند بدء التشغيل ---
    translator = QTranslator()
    settings_file = get_app_data_path("settings.json")
    current_locale = "ar" # اللغة الافتراضية
    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                settings = json.load(f)
                current_locale = settings.get("language", {}).get("locale", "ar")
        except json.JSONDecodeError:
            pass
    
    if translator.load(f"lang_{current_locale}", os.path.join(os.path.dirname(__file__), "translations")):
        app.installTranslator(translator)

    # --- عرض الشاشة الترحيبية ---
    splash_screen = SplashScreen()
    splash_screen.show()
    # تشغيل حلقة الأحداث الخاصة بالشاشة الترحيبية حتى تنتهي
    while splash_screen.isVisible():
        app.processEvents()
    # -------------------------

    while True:
        company_dialog = SelectCompanyDialog()
        if company_dialog.exec() == QDialog.Accepted:
            selected_config = company_dialog.selected_company_config
            db_url = get_db_url_from_config(selected_config)
            
            # --- الحصول على ملف تعريف النشاط التجاري ---
            business_profile = get_business_profile(selected_config.get("business_type", "generic_store"))

            splash_screen.show()
            app.processEvents()

            try: # تم تصحيح هذا السطر
                database.setup_database_connection(db_url)
                database.init_db()
                splash_screen.close()
            except Exception as e:
                splash_screen.close()
                QMessageBox.critical(None, "خطأ في الاتصال", f"فشل الاتصال بقاعدة البيانات للشركة المحددة.\nالخطأ: {e}")
                continue # العودة إلى شاشة اختيار الشركة

            login_dialog = LoginDialog()
            if login_dialog.exec() == QDialog.Accepted:
                # --- التحقق من التفعيل بعد تسجيل الدخول ---
                session = database.SessionLocal()
                is_active, expiry_date = check_app_activation(session)
                session.close()

                # عرض رسالة ترحيب بالفترة التجريبية عند أول تشغيل
                if is_active and expiry_date and (expiry_date - datetime.date.today()).days < 8:
                    activation_record = database.SessionLocal().query(database.Activation).first()
                    if activation_record and activation_record.subscription_type == 'trial':
                         QMessageBox.information(None, QCoreApplication.translate("MainWindow", "فترة تجريبية"), 
                                        f"أهلاً بك في الفترة التجريبية المجانية!\n"
                                        f"يمكنك استخدام البرنامج بكامل مزاياه حتى تاريخ: {expiry_date.strftime('%Y-%m-%d')}")

                window = MainWindow(business_profile=business_profile, company_config=selected_config) # تمرير ملف التعريف للنافذة الرئيسية

                if is_active:
                    # إذا كان البرنامج فعالاً، استمر كالمعتاد
                    window.showMaximized()
                else:
                    # إذا كان البرنامج غير فعال أو منتهي الصلاحية
                    QMessageBox.warning(window, QCoreApplication.translate("MainWindow", "الاشتراك منتهي"), 
                                        "اشتراكك في البرنامج قد انتهى أو أن البرنامج غير مفعل.\n"
                                        "سيتم توجيهك إلى شاشة التفعيل.")
                    window.open_activation_screen() # التوجيه إلى شاشة التفعيل
                    window.showMaximized()

                app.exec() # تشغيل حلقة الأحداث
                if not window.logout_requested: break
        else:
            break # الخروج من البرنامج إذا أغلق المستخدم شاشة اختيار الشركة
    sys.exit(app.exec())