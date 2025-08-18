extends Control

# Script simple pour l'écran "Hello World" de Scrabbot

func _ready():
	"""Appelé quand la scène est prête."""
	print("🎲 Scrabbot - Hello World!")

	# Configurer le label principal
	var label = $VBoxContainer/Label
	if label:
		label.text = "🎲 Bienvenue dans Scrabbot !"
		label.add_theme_font_size_override("font_size", 48)

	# Configurer le bouton
	var button = $VBoxContainer/Button
	if button:
		button.text = "Commencer"
		button.pressed.connect(_on_button_pressed)

func _on_button_pressed():
	"""Appelé quand le bouton est pressé."""
	print("Bouton pressé !")
	# TODO: Naviguer vers le menu principal
	get_tree().change_scene_to_file("res://scenes/main_menu.tscn")

func _input(event):
	"""Gère les entrées utilisateur."""
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_ESCAPE:
			get_tree().quit()
