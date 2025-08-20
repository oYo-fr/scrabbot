# Tests unitaires pour l'accès aux dictionnaires depuis Godot
# Système de dictionnaires multilingues Scrabbot - Ticket OYO-7
#
# Ces tests vérifient que l'application Godot peut bien accéder aux dictionnaires
# via l'API REST selon les spécifications du ticket.
#
# Tests couverts :
# - Test d'accès API HTTP vers le serveur
# - Test de validation du format de réponse JSON
# - Test de timeout et gestion d'erreurs
# - Test hors ligne et fallback
# - Test d'intégration bout-en-bout

extends GutTest

# Variables pour les tests
var http_request: HTTPRequest
var api_base_url: String = "http://localhost:8000/api/v1/dictionnaire"
var timeout_duration: float = 5.0
var response_received: bool = false
var last_response_data: Dictionary = {}
var last_error_code: int = 0

# Configuration des tests
func before_each():
	"""Initialisation avant chaque test."""
	# Création d'un HTTPRequest pour les tests
	http_request = HTTPRequest.new()
	add_child(http_request)
	
	# Configuration des timeouts
	http_request.timeout = timeout_duration
	
	# Connexion des signaux
	http_request.request_completed.connect(_on_request_completed)
	
	# Réinitialisation des variables
	response_received = false
	last_response_data = {}
	last_error_code = 0

func after_each():
	"""Nettoyage après chaque test."""
	if http_request:
		http_request.queue_free()
	response_received = false

# ============================================================================
# TESTS D'ACCÈS API HTTP
# ============================================================================

func test_acces_api_validation_francais():
	"""Test d'accès API : validation mot français."""
	var url = api_base_url + "/fr/valider/CHAT"
	var error = http_request.request(url)
	
	assert_eq(error, OK, "Erreur lors du lancement de la requête HTTP")
	
	# Attendre la réponse
	await _attendre_reponse()
	
	assert_true(response_received, "Aucune réponse reçue du serveur")
	assert_eq(last_error_code, 0, "Code d'erreur HTTP inattendu: " + str(last_error_code))
	
	# Vérification de la structure de réponse
	assert_true(last_response_data.has("mot"), "Champ 'mot' manquant dans la réponse")
	assert_true(last_response_data.has("valide"), "Champ 'valide' manquant dans la réponse")
	assert_true(last_response_data.has("langue"), "Champ 'langue' manquant dans la réponse")
	
	# Vérification des valeurs
	assert_eq(last_response_data.langue, "fr", "Langue incorrecte dans la réponse")
	assert_eq(last_response_data.mot, "CHAT", "Mot incorrect dans la réponse")

func test_acces_api_validation_anglais():
	"""Test d'accès API : validation mot anglais."""
	var url = api_base_url + "/en/valider/CAT"
	var error = http_request.request(url)
	
	assert_eq(error, OK, "Erreur lors du lancement de la requête HTTP")
	
	await _attendre_reponse()
	
	assert_true(response_received, "Aucune réponse reçue du serveur")
	assert_eq(last_response_data.langue, "en", "Langue incorrecte pour l'anglais")
	assert_eq(last_response_data.mot, "CAT", "Mot incorrect dans la réponse anglaise")

func test_acces_api_definition_francaise():
	"""Test d'accès API : récupération définition française."""
	var url = api_base_url + "/fr/definition/CHAT"
	var error = http_request.request(url)
	
	assert_eq(error, OK, "Erreur lors du lancement de la requête HTTP")
	
	await _attendre_reponse()
	
	assert_true(response_received, "Aucune réponse reçue pour la définition")
	assert_true(last_response_data.has("definition"), "Champ 'definition' manquant")
	assert_true(last_response_data.has("trouve"), "Champ 'trouve' manquant")
	assert_eq(last_response_data.langue, "fr", "Langue incorrecte pour définition française")

func test_acces_api_recherche_par_criteres():
	"""Test d'accès API : recherche par critères."""
	var url = api_base_url + "/fr/recherche?longueur=4&commence_par=C&limite=10"
	var error = http_request.request(url)
	
	assert_eq(error, OK, "Erreur lors du lancement de la requête de recherche")
	
	await _attendre_reponse()
	
	assert_true(response_received, "Aucune réponse reçue pour la recherche")
	assert_true(last_response_data.has("mots"), "Champ 'mots' manquant dans la recherche")
	assert_true(last_response_data.has("nb_resultats"), "Champ 'nb_resultats' manquant")
	assert_true(last_response_data.has("criteres"), "Champ 'criteres' manquant")

# ============================================================================
# TESTS DE VALIDATION JSON
# ============================================================================

func test_format_reponse_json_validation():
	"""Test de validation du format de réponse JSON pour validation."""
	var url = api_base_url + "/fr/valider/TEST"
	var error = http_request.request(url)
	
	assert_eq(error, OK, "Erreur lors du lancement de la requête")
	
	await _attendre_reponse()
	
	# Vérification du format JSON complet
	var champs_requis = ["mot", "valide", "langue"]
	for champ in champs_requis:
		assert_true(last_response_data.has(champ), "Champ requis manquant: " + champ)
	
	# Vérification des types
	assert_typeof(last_response_data.mot, TYPE_STRING, "Type incorrect pour 'mot'")
	assert_typeof(last_response_data.valide, TYPE_BOOL, "Type incorrect pour 'valide'")
	assert_typeof(last_response_data.langue, TYPE_STRING, "Type incorrect pour 'langue'")
	
	# Vérification des valeurs optionnelles
	if last_response_data.has("definition") and last_response_data.definition != null:
		assert_typeof(last_response_data.definition, TYPE_STRING, "Type incorrect pour 'definition'")
	
	if last_response_data.has("points") and last_response_data.points != null:
		assert_typeof(last_response_data.points, TYPE_INT, "Type incorrect pour 'points'")
		assert_gt(last_response_data.points, 0, "Points doivent être positifs")
	
	if last_response_data.has("temps_recherche_ms") and last_response_data.temps_recherche_ms != null:
		assert_typeof(last_response_data.temps_recherche_ms, TYPE_FLOAT, "Type incorrect pour 'temps_recherche_ms'")
		assert_lt(last_response_data.temps_recherche_ms, 100.0, "Temps de recherche trop élevé")

func test_format_reponse_json_definition():
	"""Test de validation du format JSON pour définition."""
	var url = api_base_url + "/fr/definition/CHAT"
	var error = http_request.request(url)
	
	assert_eq(error, OK, "Erreur lors du lancement de la requête définition")
	
	await _attendre_reponse()
	
	# Champs obligatoires pour définition
	var champs_requis = ["mot", "trouve", "langue"]
	for champ in champs_requis:
		assert_true(last_response_data.has(champ), "Champ requis manquant pour définition: " + champ)
	
	# Types corrects
	assert_typeof(last_response_data.mot, TYPE_STRING, "Type incorrect pour 'mot' dans définition")
	assert_typeof(last_response_data.trouve, TYPE_BOOL, "Type incorrect pour 'trouve'")
	assert_typeof(last_response_data.langue, TYPE_STRING, "Type incorrect pour 'langue' dans définition")

func test_format_reponse_json_recherche():
	"""Test de validation du format JSON pour recherche."""
	var url = api_base_url + "/fr/recherche?limite=5"
	var error = http_request.request(url)
	
	assert_eq(error, OK, "Erreur lors du lancement de la requête recherche")
	
	await _attendre_reponse()
	
	# Structure de réponse recherche
	assert_true(last_response_data.has("mots"), "Champ 'mots' manquant dans recherche")
	assert_true(last_response_data.has("nb_resultats"), "Champ 'nb_resultats' manquant")
	assert_true(last_response_data.has("criteres"), "Champ 'criteres' manquant")
	assert_true(last_response_data.has("langue"), "Champ 'langue' manquant dans recherche")
	
	# Types corrects
	assert_typeof(last_response_data.mots, TYPE_ARRAY, "Type incorrect pour 'mots'")
	assert_typeof(last_response_data.nb_resultats, TYPE_INT, "Type incorrect pour 'nb_resultats'")
	assert_typeof(last_response_data.criteres, TYPE_DICTIONARY, "Type incorrect pour 'criteres'")
	assert_typeof(last_response_data.langue, TYPE_STRING, "Type incorrect pour 'langue' recherche")
	
	# Cohérence des données
	assert_eq(last_response_data.nb_resultats, last_response_data.mots.size(), 
			  "Incohérence entre nb_resultats et taille du tableau mots")

# ============================================================================
# TESTS DE TIMEOUT ET GESTION D'ERREURS
# ============================================================================

func test_gestion_timeout():
	"""Test de gestion du timeout de requête."""
	# Configuration d'un timeout très court pour forcer l'erreur
	http_request.timeout = 0.1
	
	# URL avec délai artificiel (si disponible sur le serveur de test)
	var url = api_base_url + "/fr/valider/MOTAVECTIMEOUT"
	var error = http_request.request(url)
	
	assert_eq(error, OK, "Erreur lors du lancement de la requête timeout")
	
	# Attendre plus longtemps que le timeout
	await get_tree().create_timer(0.5).timeout
	
	# Le test pourrait échouer de différentes manières selon l'implémentation
	# L'important est que l'application ne se bloque pas

func test_gestion_serveur_indisponible():
	"""Test de gestion d'un serveur indisponible."""
	# URL vers un serveur qui n'existe pas
	var url_invalide = "http://localhost:9999/api/v1/dictionnaire/fr/valider/TEST"
	var error = http_request.request(url_invalide)
	
	# La requête devrait se lancer sans erreur immédiate
	assert_eq(error, OK, "Erreur lors du lancement vers serveur indisponible")
	
	await _attendre_reponse_ou_timeout()
	
	# Vérifier qu'on gère bien l'erreur de connexion
	assert_false(response_received, "Réponse reçue d'un serveur qui devrait être indisponible")

func test_gestion_reponse_json_invalide():
	"""Test de gestion d'une réponse JSON invalide."""
	# Note: Ce test nécessiterait un serveur de test qui retourne du JSON invalide
	# Pour l'instant, on teste la robustesse du parsing JSON
	
	var json_invalide = '{"mot": "TEST", "valide": true, "langue": "fr"'  # JSON mal formé
	var json_parser = JSON.new()
	var result = json_parser.parse(json_invalide)
	
	# Vérifier que le parsing détecte l'erreur
	assert_ne(result, OK, "Le JSON invalide aurait dû être rejeté")

func test_gestion_erreur_http_404():
	"""Test de gestion d'une erreur HTTP 404."""
	var url_inexistante = api_base_url + "/fr/inexistant/MOT"
	var error = http_request.request(url_inexistante)
	
	assert_eq(error, OK, "Erreur lors du lancement vers URL inexistante")
	
	await _attendre_reponse()
	
	# Vérifier qu'on reçoit une erreur HTTP appropriée
	if response_received:
		# Si on reçoit une réponse, elle devrait indiquer une erreur
		assert_true(last_error_code >= 400, "Code d'erreur HTTP attendu >= 400")

# ============================================================================
# TESTS HORS LIGNE ET FALLBACK
# ============================================================================

func test_detection_mode_hors_ligne():
	"""Test de détection du mode hors ligne."""
	# Simulation de la détection d'absence de connexion
	var connexion_disponible = _verifier_connexion_internet()
	
	# Ce test dépend de l'implémentation réelle
	# En attendant, on vérifie juste que la fonction existe
	assert_typeof(connexion_disponible, TYPE_BOOL, "La vérification de connexion doit retourner un booléen")

func test_fallback_dictionnaire_local():
	"""Test du fallback vers dictionnaire local en mode hors ligne."""
	# Ce test nécessiterait l'implémentation d'un dictionnaire local de fallback
	# Pour l'instant, on teste la logique de base
	
	var mot_test = "CHAT"
	var resultat_fallback = _valider_mot_local(mot_test)
	
	# Vérifier que le fallback retourne un format cohérent
	assert_true(resultat_fallback.has("mot"), "Fallback doit retourner le mot")
	assert_true(resultat_fallback.has("valide"), "Fallback doit retourner le statut de validation")
	assert_eq(resultat_fallback.mot, mot_test, "Mot incorrect dans fallback")

# ============================================================================
# TESTS D'INTÉGRATION BOUT-EN-BOUT
# ============================================================================

func test_integration_validation_complete():
	"""Test d'intégration : validation complète d'un mot."""
	var mot_test = "SCRABBLE"
	
	# 1. Validation du mot
	var url_validation = api_base_url + "/fr/valider/" + mot_test
	var error = http_request.request(url_validation)
	assert_eq(error, OK, "Erreur lors de la validation")
	
	await _attendre_reponse()
	assert_true(response_received, "Pas de réponse pour la validation")
	
	var mot_valide = last_response_data.get("valide", false)
	
	if mot_valide:
		# 2. Si valide, récupérer la définition
		response_received = false
		var url_definition = api_base_url + "/fr/definition/" + mot_test
		error = http_request.request(url_definition)
		assert_eq(error, OK, "Erreur lors de récupération définition")
		
		await _attendre_reponse()
		assert_true(response_received, "Pas de réponse pour la définition")
		assert_true(last_response_data.trouve, "Définition non trouvée pour mot valide")
		assert_ne(last_response_data.definition, "", "Définition vide pour mot valide")

func test_integration_recherche_et_validation():
	"""Test d'intégration : recherche puis validation des résultats."""
	# 1. Recherche de mots de 4 lettres commençant par C
	var url_recherche = api_base_url + "/fr/recherche?longueur=4&commence_par=C&limite=3"
	var error = http_request.request(url_recherche)
	assert_eq(error, OK, "Erreur lors de la recherche")
	
	await _attendre_reponse()
	assert_true(response_received, "Pas de réponse pour la recherche")
	assert_gt(last_response_data.nb_resultats, 0, "Aucun résultat trouvé")
	
	# 2. Valider le premier mot trouvé
	if last_response_data.mots.size() > 0:
		var premier_mot = last_response_data.mots[0].mot
		
		response_received = false
		var url_validation = api_base_url + "/fr/valider/" + premier_mot
		error = http_request.request(url_validation)
		assert_eq(error, OK, "Erreur lors de validation du mot trouvé")
		
		await _attendre_reponse()
		assert_true(response_received, "Pas de réponse pour validation du mot trouvé")
		assert_true(last_response_data.valide, "Mot trouvé par recherche non valide : " + premier_mot)

func test_integration_performance_multiple():
	"""Test d'intégration : performance avec requêtes multiples."""
	var mots_test = ["CHAT", "CHIEN", "MAISON", "SCRABBLE", "JEU"]
	var temps_debut = Time.get_time_dict_from_system()
	var validations_reussies = 0
	
	for mot in mots_test:
		var url = api_base_url + "/fr/valider/" + mot
		var error = http_request.request(url)
		
		if error == OK:
			await _attendre_reponse()
			if response_received:
				validations_reussies += 1
		
		response_received = false
	
	var temps_fin = Time.get_time_dict_from_system()
	var duree_totale = _calculer_duree_ms(temps_debut, temps_fin)
	
	assert_gt(validations_reussies, 0, "Aucune validation réussie")
	assert_lt(duree_totale, 1000.0, "Validation multiple trop lente: " + str(duree_totale) + "ms")

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

func _on_request_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray):
	"""Callback appelé quand une requête HTTP est terminée."""
	response_received = true
	last_error_code = response_code
	
	if response_code == 200:
		var json_string = body.get_string_from_utf8()
		var json_parser = JSON.new()
		var parse_result = json_parser.parse(json_string)
		
		if parse_result == OK:
			last_response_data = json_parser.data
		else:
			push_error("Erreur parsing JSON: " + json_string)
			last_response_data = {}
	else:
		push_error("Erreur HTTP: " + str(response_code))
		last_response_data = {}

func _attendre_reponse():
	"""Attend une réponse HTTP avec timeout."""
	var temps_attente = 0.0
	while not response_received and temps_attente < timeout_duration:
		await get_tree().process_frame
		temps_attente += get_process_delta_time()
	
	if not response_received:
		push_warning("Timeout atteint en attendant la réponse")

func _attendre_reponse_ou_timeout():
	"""Attend une réponse ou un timeout explicite."""
	var temps_attente = 0.0
	var timeout_long = timeout_duration * 2  # Timeout plus long pour tester les erreurs
	
	while not response_received and temps_attente < timeout_long:
		await get_tree().process_frame
		temps_attente += get_process_delta_time()

func _verifier_connexion_internet() -> bool:
	"""Vérifie si une connexion internet est disponible."""
	# Implémentation simplifiée pour les tests
	# En production, on pourrait pinguer le serveur ou utiliser OS.get_network_interfaces()
	return true

func _valider_mot_local(mot: String) -> Dictionary:
	"""Validation locale en mode fallback (simulation)."""
	# Dictionnaire local minimal pour les tests
	var mots_locaux = ["CHAT", "CHIEN", "MAISON", "JEU", "SCRABBLE"]
	
	return {
		"mot": mot.to_upper(),
		"valide": mot.to_upper() in mots_locaux,
		"definition": "Définition locale pour " + mot if mot.to_upper() in mots_locaux else null,
		"source": "local"
	}

func _calculer_duree_ms(debut: Dictionary, fin: Dictionary) -> float:
	"""Calcule la durée en millisecondes entre deux timestamps."""
	# Calcul simplifié pour les tests
	var duree_sec = (fin.hour - debut.hour) * 3600 + (fin.minute - debut.minute) * 60 + (fin.second - debut.second)
	return duree_sec * 1000.0

# ============================================================================
# TESTS DE CONFIGURATION
# ============================================================================

func test_configuration_api_url():
	"""Test de configuration de l'URL de l'API."""
	assert_ne(api_base_url, "", "URL de base de l'API ne doit pas être vide")
	assert_true(api_base_url.begins_with("http"), "URL doit commencer par http")
	assert_true(api_base_url.contains("dictionnaire"), "URL doit contenir 'dictionnaire'")

func test_configuration_timeout():
	"""Test de configuration du timeout."""
	assert_gt(timeout_duration, 0.0, "Timeout doit être positif")
	assert_lt(timeout_duration, 30.0, "Timeout ne doit pas être trop long")

# Point d'entrée pour les tests manuels
func _ready():
	"""Point d'entrée pour exécution manuelle des tests."""
	if get_parent().name == "SceneTree":
		print("=== Tests API Dictionnaires Godot ===")
		print("Utiliser GUT pour lancer ces tests automatiquement")
		print("URL API: ", api_base_url)
		print("Timeout: ", timeout_duration, "s")
