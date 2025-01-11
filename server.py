import asyncio
import websockets
import json
import time
import sqlite3
from dataclasses import dataclass
from typing import Optional, Dict, List
from datetime import datetime
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableWidgetItem, 
                             QVBoxLayout, QLabel, QTableWidget, QWidget, QLineEdit, QPushButton)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ServerConfig:
    """Server configuration"""
    host: str = "192.168.1.2"
    port: int = 8765
    db_path: str = "machine_ids.db"
    inactive_timeout: int = 300  # 5 minutes

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()

    # In the DatabaseManager class, update the init_db method:
    def init_db(self):
        """Initialize database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS authorized_machines (
                        machine_id TEXT PRIMARY KEY,
                        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'inactive'
                    )
                """)
                conn.commit()
                logger.info("Database initialized successfully.")
        except sqlite3.Error as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    def add_machine(self, machine_id: str) -> bool:
        """Add new machine to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO authorized_machines (machine_id, last_active, status) VALUES (?, ?, ?)",
                    (machine_id, int(time.time()), "active")
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Failed to add machine {machine_id}: {e}")
            return False

    # Update the update_machine_status method:
    def update_machine_status(self, machine_id: str, status: str = "active") -> None:
        """Update machine's status and timestamp"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO authorized_machines (machine_id, status, last_active)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(machine_id) DO UPDATE SET 
                        status=?, 
                        last_active=CURRENT_TIMESTAMP
                """, (machine_id, status, status))
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to update machine status {machine_id}: {e}")

    def get_all_machines(self) -> List[Dict]:
        """Get all registered machines with their status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT machine_id, last_active, status 
                    FROM authorized_machines
                    ORDER BY last_active DESC
                """)
                return [
                    {
                        "machine_id": row[0],
                        "last_active": datetime.fromtimestamp(row[1]).strftime('%Y-%m-%d %H:%M:%S'),
                        "status": row[2]
                    }
                    for row in cursor.fetchall()
                ]
        except sqlite3.Error as e:
            logger.error(f"Failed to fetch machines: {e}")
            return []

    def cleanup_inactive(self, timeout: int) -> None:
        """Remove inactive machines"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE authorized_machines SET status = 'inactive' WHERE last_active < ?",
                    (int(time.time()) - timeout,)
                )
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to cleanup inactive machines: {e}")

class Dashboard(QMainWindow):
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db_manager = db_manager
        self.init_ui()
        self.setup_auto_refresh()

    def init_ui(self):
        self.setWindowTitle("Agent Management Dashboard")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Header
        self.label = QLabel("Connected Agents")
        self.label.setFont(QFont("Arial", 16, QFont.Bold))
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        # Input section
        self.input_machine_id = QLineEdit()
        self.input_machine_id.setPlaceholderText("Enter Machine ID")
        self.input_machine_id.setFont(QFont("Arial", 12))
        layout.addWidget(self.input_machine_id)

        self.btn_authorize = QPushButton("Authorize")
        self.btn_authorize.setFont(QFont("Arial", 12))
        self.btn_authorize.clicked.connect(self.authorize_machine)
        layout.addWidget(self.btn_authorize)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Machine ID", "Last Active", "Status"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, header.Stretch)
        header.setSectionResizeMode(1, header.Stretch)
        header.setSectionResizeMode(2, header.Stretch)
        layout.addWidget(self.table)
            
        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_table)
        layout.addWidget(self.refresh_button)

        self.refresh_table()

    def setup_auto_refresh(self):
        """Setup automatic refresh timer"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_table)
        self.timer.start(5000)  # Refresh every 5 seconds

    def refresh_table(self):
        """Refresh the dashboard table"""
        machines = self.db_manager.get_all_machines()
        self.table.setRowCount(len(machines))
        for row, machine in enumerate(machines):
            self.table.setItem(row, 0, QTableWidgetItem(machine["machine_id"]))
            self.table.setItem(row, 1, QTableWidgetItem(machine["last_active"]))
            status_item = QTableWidgetItem(machine["status"])
            status_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, status_item)

    def authorize_machine(self):
        """Handle machine authorization"""
        machine_id = self.input_machine_id.text().strip()
        if not machine_id:
            logger.warning("Machine ID cannot be empty")
            return

        if self.db_manager.add_machine(machine_id):
            logger.info(f"Machine ID '{machine_id}' has been authorized")
            self.input_machine_id.clear()
            self.refresh_table()
        else:
            logger.error(f"Failed to authorize machine ID '{machine_id}'")

class Server:
    def __init__(self, config: ServerConfig):
        self.config = config
        self.db_manager = DatabaseManager(config.db_path)
        logger.info("Server initialized without ML models")

    async def handle_agent(self, websocket):
        machine_id = None
        try:
            message = await websocket.recv()
            data = json.loads(message)
            machine_id = data.get('machine_id')

            if not machine_id:
                await websocket.send(json.dumps({"status": "rejected"}))
                return

            self.db_manager.add_machine(machine_id)
            await websocket.send(json.dumps({"status": "approved"}))
            async for message in websocket:
                data = json.loads(message)
                self.db_manager.update_machine_status(machine_id)
                await websocket.send(json.dumps({"status": "received"}))

        except websockets.ConnectionClosed:
            pass
        except Exception as e:
            logger.error(f"Error handling agent: {e}")

    async def start(self):
        """Start WebSocket server"""
        async with websockets.serve(
            self.handle_agent,
            self.config.host,
            self.config.port,
            ping_interval=None,  # Disable ping to avoid timeouts
            close_timeout=10
        ):
            await asyncio.Future()  # run forever

def main():
    """Main entry point"""
    config = ServerConfig()
    server = Server(config)
    
    app = QApplication([])
    dashboard = Dashboard(server.db_manager)
    dashboard.show()

    # Run server and GUI
    loop = asyncio.get_event_loop()
    loop.create_task(server.start())
    
    # Start periodic cleanup
    def cleanup():
        server.db_manager.cleanup_inactive(config.inactive_timeout)
    
    cleanup_timer = QTimer()
    cleanup_timer.timeout.connect(cleanup)
    cleanup_timer.start(60000)  # Run cleanup every minute
    
    try:
        app.exec_()
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    finally:
        loop.close()

if __name__ == "__main__":
    main()