# File path: /mnt/data/main.py
import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5.uic import loadUi
import pyrebase

# Firebase configuration
firebaseConfig = {
    'apiKey': "AIzaSyCUUpbrZqMnY2iiVuCEvHWK0FQGa2CFdSg",
    'authDomain': "cyber-sentinal.firebaseapp.com",
    'databaseURL': "https://cyber-sentinal-default-rtdb.firebaseio.com",
    'projectId': "cyber-sentinal",
    'storageBucket': "cyber-sentinal.firebasestorage.app",
    'messagingSenderId': "47655652949",
    'appId': "1:47655652949:web:fad843aa171d209d7ccedc",
    'measurementId': "G-PTTFV79FCF"
}

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

class Login(QDialog):
    def __init__(self):
        super(Login, self).__init__()
        loadUi("login.ui", self)
        self.login.clicked.connect(self.loginfunction)
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.clickhere.clicked.connect(self.gotocreate)

    def loginfunction(self):
        email = self.email.text()
        password = self.password.text()
        try:
            auth.sign_in_with_email_and_password(email, password)
            # Navigate to the dashboard and pass the user email
            dashboard = Dashboard(email)
            widget.addWidget(dashboard)
            widget.setCurrentIndex(widget.currentIndex() + 1)
        except Exception as e:
            if hasattr(self, "label_invalid"):  # Check if label_invalid exists
                self.label_invalid.setText("Invalid email or password.")
                self.label_invalid.setStyleSheet("color: red;")
                self.label_invalid.setVisible(True)


    def gotocreate(self):
        createacc = CreateAcc()
        widget.addWidget(createacc)
        widget.setCurrentIndex(widget.currentIndex() + 1)

class CreateAcc(QDialog):
    def __init__(self):
        super(CreateAcc, self).__init__()
        loadUi("createacc.ui", self)
        self.confirmacc.clicked.connect(self.createaccfunction)
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.confirmpass.setEchoMode(QtWidgets.QLineEdit.Password)

    def createaccfunction(self):
        email = self.email.text()
        password = self.password.text()
        confirm_password = self.confirmpass.text()

        if password != confirm_password:
            self.label_invalid.setText("Passwords do not match.")
            self.label_invalid.setStyleSheet("color: red;")
            return

        try:
            auth.create_user_with_email_and_password(email, password)
            # Navigate back to login after successful signup
            login = Login()
            widget.addWidget(login)
            widget.setCurrentIndex(widget.currentIndex() - 1)
        except Exception as e:
            self.label_invalid.setText("Failed to create account.")
            self.label_invalid.setStyleSheet("color: red;")
            self.label_invalid.setVisible(True)

class Dashboard(QDialog):
    def __init__(self, user_email):
        super(Dashboard, self).__init__()
        loadUi("dashboard.ui", self)
        self.user_email = user_email
        self.welcomeLabel.setText(f"Welcome, {self.user_email}")
        self.logoutButton.clicked.connect(self.logout)

    def logout(self):
        # Navigate back to the login screen
        login = Login()
        widget.addWidget(login)
        widget.setCurrentIndex(widget.currentIndex() + 1)

app = QApplication(sys.argv)
mainwindow = Login()
widget = QtWidgets.QStackedWidget()
widget.addWidget(mainwindow)
widget.setFixedWidth(480)
widget.setFixedHeight(620)
widget.show()
sys.exit(app.exec_())
