import sys
import psutil
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, Property, QRectF, QEasingCurve, QPointF, QSequentialAnimationGroup
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient, QPolygonF
from PySide6.QtWidgets import QApplication, QWidget

class BatteryWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._animated_percent = 0.0
        self._pulse_scale = 1.0
        self.plugged = False
        self.prev_plugged = False

        self.initUI()
        self.initAnimation()
        
        self.update_battery_info() # Initial call
        
        # Timer to update battery info every 1 second for responsiveness
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_battery_info)
        self.timer.start(1000)

    def initUI(self):
        # --- Window Setup (Smaller) ---
        self.setFixedSize(120, 120)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # --- Positioning ---
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - self.width() - 20, 30)
        
    def initAnimation(self):
        # Animation for the battery percentage
        self.animation = QPropertyAnimation(self, b"animated_percent")
        self.animation.setDuration(1000)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)

        # Animation for the "plug-in" pulse effect
        self.pulse_animation_group = QSequentialAnimationGroup(self)
        anim_grow = QPropertyAnimation(self, b"pulse_scale")
        anim_grow.setDuration(150)
        anim_grow.setStartValue(1.0)
        anim_grow.setEndValue(1.1)
        anim_grow.setEasingCurve(QEasingCurve.OutCubic)
        anim_shrink = QPropertyAnimation(self, b"pulse_scale")
        anim_shrink.setDuration(250)
        anim_shrink.setStartValue(1.1)
        anim_shrink.setEndValue(1.0)
        anim_shrink.setEasingCurve(QEasingCurve.InCubic)
        self.pulse_animation_group.addAnimation(anim_grow)
        self.pulse_animation_group.addAnimation(anim_shrink)

    def get_animated_percent(self):
        return self._animated_percent

    def set_animated_percent(self, value):
        self._animated_percent = value
        self.update()

    animated_percent = Property(float, get_animated_percent, set_animated_percent)

    def get_pulse_scale(self):
        return self._pulse_scale

    def set_pulse_scale(self, value):
        self._pulse_scale = value
        self.update()
    
    pulse_scale = Property(float, get_pulse_scale, set_pulse_scale)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # --- Progress Arc (Thinner) ---
        base_rect = self.rect().adjusted(10, 10, -10, -10)
        # Apply pulse animation scale
        center = base_rect.center()
        width = base_rect.width() * self._pulse_scale
        height = base_rect.height() * self._pulse_scale
        rect = QRectF(0, 0, width, height)
        rect.moveCenter(center)

        percent = self._animated_percent
        
        # Determine Colors based on percentage
        if self.plugged:
            color1, color2 = "#69F0AE", "#00C853" # Charging Green
        elif percent < 20:
            color1, color2 = "#F44336", "#D32F2F" # Low battery Red
        elif percent < 50:
            color1, color2 = "#FFC107", "#FFA000" # Medium battery Yellow
        else:
            color1, color2 = "#00E5FF", "#00B8D4" # High battery Cyan
            
        # Gradient for the arc
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, QColor(color1))
        gradient.setColorAt(1, QColor(color2))

        # Draw background arc (full circle)
        pen = QPen(QColor(60, 60, 60, 200), 10, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen)
        start_angle = 90 * 16 # Start from the top
        span_angle = 360 * 16  # Full 360 degree arc
        painter.drawArc(rect, start_angle, span_angle)
        
        # Draw progress arc
        pen.setBrush(gradient)
        painter.setPen(pen)
        progress_span = -percent / 100.0 * span_angle
        painter.drawArc(rect, start_angle, progress_span)

        # --- Central Battery Icon ---
        self.draw_battery_icon(painter, percent, color1, color2)

        # --- Text (Inside Circle) ---
        font = QFont("Segoe UI", 9, QFont.Bold)
        painter.setFont(font)
        painter.setPen(Qt.white)
        # Define a rect for the text below the battery icon
        text_rect = self.rect().adjusted(0, 80, 0, -15)
        painter.drawText(text_rect, Qt.AlignCenter, f"{int(percent)}%")
        
    def draw_battery_icon(self, painter, percent, color1, color2):
        # Scaled down and repositioned coordinates
        # Battery outer body
        body_rect = QRectF(45, 35, 30, 45)
        painter.setBrush(QColor(40, 40, 40, 200))
        painter.setPen(QPen(QColor(200, 200, 200), 1.5))
        painter.drawRoundedRect(body_rect, 3, 3)

        # Battery top cap
        cap_rect = QRectF(51, 31, 18, 4)
        painter.drawRoundedRect(cap_rect, 2, 2)
        
        # Battery fill level
        fill_height = (body_rect.height() - 4) * (percent / 100.0)
        fill_rect = QRectF(
            body_rect.left() + 2, 
            body_rect.bottom() - 2 - fill_height,
            body_rect.width() - 4,
            fill_height
        )
        
        # Gradient for the fill
        fill_gradient = QLinearGradient(fill_rect.topLeft(), fill_rect.bottomLeft())
        fill_gradient.setColorAt(0, QColor(color1))
        fill_gradient.setColorAt(1, QColor(color2))

        painter.setBrush(fill_gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(fill_rect, 2, 2)

        # Draw charging symbol if plugged in
        if self.plugged:
            painter.setBrush(QColor(255, 255, 255, 220)) # Semi-transparent white
            painter.setPen(Qt.NoPen)
            points = [
                QPointF(57, 48), QPointF(63, 48), QPointF(60, 57), 
                QPointF(63, 57), QPointF(57, 70), QPointF(60, 61), 
                QPointF(57, 61)
            ]
            polygon = QPolygonF(points)
            painter.drawPolygon(polygon)

    def update_battery_info(self):
        try:
            battery = psutil.sensors_battery()
            target_percent = int(battery.percent) if battery else 0
            self.plugged = battery.power_plugged if battery else False
            
            # Check if the plugged-in state has just changed to True
            if self.plugged and not self.prev_plugged:
                self.pulse_animation_group.start()
            
            self.prev_plugged = self.plugged

            self.animation.stop()
            self.animation.setStartValue(self._animated_percent)
            self.animation.setEndValue(target_percent)
            self.animation.start()

        except Exception as e:
            print(f"Error fetching battery info: {e}")

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = BatteryWidget()
    widget.show()
    sys.exit(app.exec())

