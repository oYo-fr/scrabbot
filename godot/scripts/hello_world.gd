extends Control

# Simple script for Scrabbot "Hello World" screen

func _ready():
	"""Called when the scene is ready."""
	print("🎲 Scrabbot - Hello World!")

	# Configure main label
	var label = $VBoxContainer/Label
	if label:
		label.text = "🎲 Welcome to Scrabbot!"
		label.add_theme_font_size_override("font_size", 48)

	# Configure button
	var button = $VBoxContainer/Button
	if button:
		button.text = "Start"
		button.pressed.connect(_on_button_pressed)

func _on_button_pressed():
	"""Called when button is pressed."""
	print("Button pressed!")
	# TODO: Navigate to main menu
	get_tree().change_scene_to_file("res://scenes/main_menu.tscn")

func _input(event):
	"""Handle user input."""
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_ESCAPE:
			get_tree().quit()
