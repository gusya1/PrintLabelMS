from PyQt5 import QtGui


def apply_ui_scale(app, ui_scale):
    """Масштабирует шрифт приложения коэффициентом ui_scale; layout'ы растягивают виджеты."""
    if ui_scale == 1.0:
        return
    base_font = app.font()
    scaled_font = QtGui.QFont(base_font)
    if base_font.pointSizeF() > 0:
        scaled_font.setPointSizeF(base_font.pointSizeF() * ui_scale)
    else:
        scaled_font.setPixelSize(max(1, round(base_font.pixelSize() * ui_scale)))
    app.setFont(scaled_font)
