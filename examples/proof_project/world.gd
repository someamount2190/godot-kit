extends Node2D
# A PASSIVE target scene (like a real game scene): builds content, never quits.
# The godot-kit harness controls capture + quit.
func _ready() -> void:
	var bg := ColorRect.new()
	bg.color = Color(0.08, 0.28, 0.20)
	bg.size = Vector2(640, 360)
	add_child(bg)
	for i in 5:
		var c := ColorRect.new()
		c.color = Color(0.2 + 0.15 * i, 0.6, 0.9 - 0.12 * i)
		c.size = Vector2(60, 60)
		c.position = Vector2(40 + i * 110, 150)
		add_child(c)
	var lbl := Label.new()
	lbl.text = "passive target scene"
	lbl.position = Vector2(220, 60)
	lbl.add_theme_font_size_override("font_size", 24)
	add_child(lbl)
