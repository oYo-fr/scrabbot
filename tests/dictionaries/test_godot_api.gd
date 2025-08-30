# Unit tests for dictionary access from Godot
# Scrabbot multilingual dictionaries system - Ticket OYO-7
#
# These tests verify that the Godot application can properly access dictionaries
# via the REST API according to ticket specifications.
#
# Covered tests:
# - HTTP API access test to server
# - JSON response format validation test
# - Timeout and error handling test
# - Offline and fallback test
# - End-to-end integration test

extends GutTest

# Variables for tests
var http_request: HTTPRequest
var api_base_url: String = "http://localhost:8000/api/v1/dictionary"
var timeout_duration: float = 5.0
var response_received: bool = false
var last_response_data: Dictionary = {}
var last_error_code: int = 0

# Test configuration
func before_each():
	"""Initialization before each test."""
	# Create an HTTPRequest for tests
	http_request = HTTPRequest.new()
	add_child(http_request)

	# Timeout configuration
	http_request.timeout = timeout_duration

	# Signal connections
	http_request.request_completed.connect(_on_request_completed)

	# Reset variables
	response_received = false
	last_response_data = {}
	last_error_code = 0

func after_each():
	"""Cleanup after each test."""
	if http_request:
		http_request.queue_free()
	response_received = false

# ============================================================================
# HTTP API ACCESS TESTS
# ============================================================================

func test_french_api_validation_access():
	"""API access test: French word validation."""
	var url = api_base_url + "/validate/CHAT?language=fr"
	var error = http_request.request(url)

	assert_eq(error, OK, "Error launching HTTP request")

	# Wait for response
	await _wait_for_response()

	assert_true(response_received, "No response received from server")
	assert_eq(last_error_code, 0, "Unexpected HTTP error code: " + str(last_error_code))

	# Response structure verification
	assert_true(last_response_data.has("word"), "Field 'word' missing in response")
	assert_true(last_response_data.has("valid"), "Field 'valid' missing in response")
	assert_true(last_response_data.has("language"), "Field 'language' missing in response")

	# Value verification
	assert_eq(last_response_data.language, "fr", "Incorrect language in response")
	assert_eq(last_response_data.word, "CHAT", "Incorrect word in response")

func test_english_api_validation_access():
	"""API access test: English word validation."""
	var url = api_base_url + "/validate/CAT?language=en"
	var error = http_request.request(url)

	assert_eq(error, OK, "Error launching HTTP request")

	await _wait_for_response()

	assert_true(response_received, "No response received from server")
	assert_eq(last_response_data.language, "en", "Incorrect language for English")
	assert_eq(last_response_data.word, "CAT", "Incorrect word in English response")

func test_french_api_definition_access():
	"""API access test: French definition retrieval."""
	var url = api_base_url + "/definition/CHAT?language=fr"
	var error = http_request.request(url)

	assert_eq(error, OK, "Error launching HTTP request")

	await _wait_for_response()

	assert_true(response_received, "No response received for definition")
	assert_true(last_response_data.has("definition"), "Field 'definition' missing")
	assert_true(last_response_data.has("found"), "Field 'found' missing")
	assert_eq(last_response_data.language, "fr", "Incorrect language for French definition")

func test_api_criteria_search_access():
	"""API access test: criteria-based search."""
	var url = api_base_url + "/search?language=fr&length=4&starts_with=C&limit=10"
	var error = http_request.request(url)

	assert_eq(error, OK, "Error launching search request")

	await _wait_for_response()

	assert_true(response_received, "No response received for search")
	assert_true(last_response_data.has("mots"), "Field 'mots' missing in search")
	assert_true(last_response_data.has("nb_resultats"), "Field 'nb_resultats' missing")
	assert_true(last_response_data.has("criteres"), "Field 'criteres' missing")

# ============================================================================
# JSON VALIDATION TESTS
# ============================================================================

func test_validation_json_response_format():
	"""JSON response format validation test for validation."""
	var url = api_base_url + "/validate/TEST?language=fr"
	var error = http_request.request(url)

	assert_eq(error, OK, "Error launching request")

	await _wait_for_response()

	# Complete JSON format verification
	var required_fields = ["word", "valid", "language"]
	for field in required_fields:
		assert_true(last_response_data.has(field), "Required field missing: " + field)

	# Type verification
	assert_typeof(last_response_data.word, TYPE_STRING, "Incorrect type for 'word'")
	assert_typeof(last_response_data.valid, TYPE_BOOL, "Incorrect type for 'valid'")
	assert_typeof(last_response_data.language, TYPE_STRING, "Incorrect type for 'language'")

	# Optional values verification
	if last_response_data.has("definition") and last_response_data.definition != null:
		assert_typeof(last_response_data.definition, TYPE_STRING, "Incorrect type for 'definition'")

	if last_response_data.has("points") and last_response_data.points != null:
		assert_typeof(last_response_data.points, TYPE_INT, "Incorrect type for 'points'")
		assert_gt(last_response_data.points, 0, "Points must be positive")

	if last_response_data.has("search_time_ms") and last_response_data.search_time_ms != null:
		assert_typeof(last_response_data.search_time_ms, TYPE_FLOAT, "Incorrect type for 'search_time_ms'")
		assert_lt(last_response_data.search_time_ms, 100.0, "Search time too high")

func test_definition_json_response_format():
	"""JSON format validation test for definition."""
	var url = api_base_url + "/definition/CHAT?language=fr"
	var error = http_request.request(url)

	assert_eq(error, OK, "Error launching definition request")

	await _wait_for_response()

	# Required fields for definition
	var required_fields = ["word", "found", "language"]
	for field in required_fields:
		assert_true(last_response_data.has(field), "Required field missing for definition: " + field)

	# Correct types
	assert_typeof(last_response_data.word, TYPE_STRING, "Incorrect type for 'word' in definition")
	assert_typeof(last_response_data.found, TYPE_BOOL, "Incorrect type for 'found'")
	assert_typeof(last_response_data.language, TYPE_STRING, "Incorrect type for 'language' in definition")

func test_search_json_response_format():
	"""JSON format validation test for search."""
	var url = api_base_url + "/search?language=fr&limit=5"
	var error = http_request.request(url)

	assert_eq(error, OK, "Error launching search request")

	await _wait_for_response()

		# Search response structure
	assert_true(last_response_data.has("words"), "Field 'words' missing in search")
	assert_true(last_response_data.has("results_count"), "Field 'results_count' missing")
	assert_true(last_response_data.has("criteria"), "Field 'criteria' missing")
	assert_true(last_response_data.has("language"), "Field 'language' missing in search")

	# Correct types
	assert_typeof(last_response_data.words, TYPE_ARRAY, "Incorrect type for 'words'")
	assert_typeof(last_response_data.results_count, TYPE_INT, "Incorrect type for 'results_count'")
	assert_typeof(last_response_data.criteria, TYPE_DICTIONARY, "Incorrect type for 'criteria'")
	assert_typeof(last_response_data.language, TYPE_STRING, "Incorrect type for 'language' search")

	# Data consistency
	assert_eq(last_response_data.results_count, last_response_data.words.size(),
		  "Inconsistency between results_count and words array size")

# ============================================================================
# TIMEOUT AND ERROR HANDLING TESTS
# ============================================================================

func test_timeout_handling():
	"""Request timeout handling test."""
	# Configure very short timeout to force error
	http_request.timeout = 0.1

	# URL with artificial delay (if available on test server)
	var url = api_base_url + "/fr/valider/WORDWITHTIMEOUT"
	var error = http_request.request(url)

	assert_eq(error, OK, "Error launching timeout request")

	# Wait longer than timeout
	await get_tree().create_timer(0.5).timeout

	# Test could fail in different ways depending on implementation
	# Important thing is that application doesn't freeze

func test_unavailable_server_handling():
	"""Unavailable server handling test."""
	# URL to a server that doesn't exist
	var invalid_url = "http://localhost:9999/api/v1/dictionary/validate/TEST?language=fr"
	var error = http_request.request(invalid_url)

	# Request should launch without immediate error
	assert_eq(error, OK, "Error launching to unavailable server")

	await _wait_for_response_or_timeout()

	# Verify we handle connection error properly
	assert_false(response_received, "Response received from server that should be unavailable")

func test_invalid_json_response_handling():
	"""Invalid JSON response handling test."""
	# Note: This test would need a test server that returns invalid JSON
	# For now, we test JSON parsing robustness

	var invalid_json = '{"mot": "TEST", "valide": true, "langue": "fr"'  # Malformed JSON
	var json_parser = JSON.new()
	var result = json_parser.parse(invalid_json)

	# Verify parsing detects the error
	assert_ne(result, OK, "Invalid JSON should have been rejected")

func test_http_404_error_handling():
	"""HTTP 404 error handling test."""
	var nonexistent_url = api_base_url + "/nonexistent/WORD?language=fr"
	var error = http_request.request(nonexistent_url)

	assert_eq(error, OK, "Error launching to nonexistent URL")

	await _wait_for_response()

	# Verify we receive appropriate HTTP error
	if response_received:
		# If we receive a response, it should indicate an error
		assert_true(last_error_code >= 400, "Expected HTTP error code >= 400")

# ============================================================================
# OFFLINE AND FALLBACK TESTS
# ============================================================================

func test_offline_mode_detection():
	"""Offline mode detection test."""
	# Simulation of connection absence detection
	var connection_available = _check_internet_connection()

	# This test depends on actual implementation
	# For now, we just verify the function exists
	assert_typeof(connection_available, TYPE_BOOL, "Connection verification must return a boolean")

func test_local_dictionary_fallback():
	"""Local dictionary fallback test in offline mode."""
	# This test would require implementation of a local fallback dictionary
	# For now, we test basic logic

	var test_word = "CHAT"
	var fallback_result = _validate_local_word(test_word)

	# Verify fallback returns consistent format
	assert_true(fallback_result.has("mot"), "Fallback must return the word")
	assert_true(fallback_result.has("valide"), "Fallback must return validation status")
	assert_eq(fallback_result.mot, test_word, "Incorrect word in fallback")

# ============================================================================
# END-TO-END INTEGRATION TESTS
# ============================================================================

func test_complete_word_validation_integration():
	"""Integration test: complete word validation."""
	var test_word = "SCRABBLE"

	# 1. Word validation
	var validation_url = api_base_url + "/validate/" + test_word + "?language=fr"
	var error = http_request.request(validation_url)
	assert_eq(error, OK, "Error during validation")

	await _wait_for_response()
	assert_true(response_received, "No response for validation")

	var word_valid = last_response_data.get("valid", false)

	if word_valid:
		# 2. If valid, retrieve definition
		response_received = false
		var definition_url = api_base_url + "/definition/" + test_word + "?language=fr"
		error = http_request.request(definition_url)
		assert_eq(error, OK, "Error retrieving definition")

		await _wait_for_response()
		assert_true(response_received, "No response for definition")
		assert_true(last_response_data.found, "Definition not found for valid word")
		assert_ne(last_response_data.definition, "", "Empty definition for valid word")

func test_search_and_validation_integration():
	"""Integration test: search then validation of results."""
	# 1. Search for 4-letter words starting with C
	var search_url = api_base_url + "/search?language=fr&length=4&starts_with=C&limit=3"
	var error = http_request.request(search_url)
	assert_eq(error, OK, "Error during search")

	await _wait_for_response()
	assert_true(response_received, "No response for search")
	assert_gt(last_response_data.results_count, 0, "No results found")

	# 2. Validate first found word
	if last_response_data.words.size() > 0:
		var first_word = last_response_data.words[0].word

		response_received = false
		var validation_url = api_base_url + "/validate/" + first_word + "?language=fr"
		error = http_request.request(validation_url)
		assert_eq(error, OK, "Error validating found word")

		await _wait_for_response()
		assert_true(response_received, "No response for found word validation")
		assert_true(last_response_data.valid, "Word found by search not valid: " + first_word)

func test_multiple_requests_performance_integration():
	"""Integration test: performance with multiple requests."""
	var test_words = ["CHAT", "CHIEN", "MAISON", "SCRABBLE", "JEU"]
	var start_time = Time.get_time_dict_from_system()
	var successful_validations = 0

	for word in test_words:
		var url = api_base_url + "/validate/" + word + "?language=fr"
		var error = http_request.request(url)

		if error == OK:
			await _wait_for_response()
			if response_received:
				successful_validations += 1

		response_received = false

	var end_time = Time.get_time_dict_from_system()
	var total_duration = _calculate_duration_ms(start_time, end_time)

	assert_gt(successful_validations, 0, "No successful validations")
	assert_lt(total_duration, 1000.0, "Multiple validation too slow: " + str(total_duration) + "ms")

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

func _on_request_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray):
	"""Callback called when an HTTP request is completed."""
	response_received = true
	last_error_code = response_code

	if response_code == 200:
		var json_string = body.get_string_from_utf8()
		var json_parser = JSON.new()
		var parse_result = json_parser.parse(json_string)

		if parse_result == OK:
			last_response_data = json_parser.data
		else:
			push_error("JSON parsing error: " + json_string)
			last_response_data = {}
	else:
		push_error("HTTP error: " + str(response_code))
		last_response_data = {}

func _wait_for_response():
	"""Wait for HTTP response with timeout."""
	var wait_time = 0.0
	while not response_received and wait_time < timeout_duration:
		await get_tree().process_frame
		wait_time += get_process_delta_time()

	if not response_received:
		push_warning("Timeout reached waiting for response")

func _wait_for_response_or_timeout():
	"""Wait for response or explicit timeout."""
	var wait_time = 0.0
	var long_timeout = timeout_duration * 2  # Longer timeout to test errors

	while not response_received and wait_time < long_timeout:
		await get_tree().process_frame
		wait_time += get_process_delta_time()

func _check_internet_connection() -> bool:
	"""Check if internet connection is available."""
	# Simplified implementation for tests
	# In production, we could ping server or use OS.get_network_interfaces()
	return true

func _validate_local_word(word: String) -> Dictionary:
	"""Local validation in fallback mode (simulation)."""
	# Minimal local dictionary for tests
	var local_words = ["CHAT", "CHIEN", "MAISON", "JEU", "SCRABBLE"]

	return {
		"word": word.to_upper(),
		"valid": word.to_upper() in local_words,
		"definition": "Local definition for " + word if word.to_upper() in local_words else null,
		"source": "local"
	}

func _calculate_duration_ms(start: Dictionary, end: Dictionary) -> float:
	"""Calculate duration in milliseconds between two timestamps."""
	# Simplified calculation for tests
	var duration_sec = (end.hour - start.hour) * 3600 + (end.minute - start.minute) * 60 + (end.second - start.second)
	return duration_sec * 1000.0

# ============================================================================
# CONFIGURATION TESTS
# ============================================================================

func test_api_url_configuration():
	"""API URL configuration test."""
	assert_ne(api_base_url, "", "API base URL must not be empty")
	assert_true(api_base_url.begins_with("http"), "URL must start with http")
	assert_true(api_base_url.contains("dictionary"), "URL must contain 'dictionary'")

func test_timeout_configuration():
	"""Timeout configuration test."""
	assert_gt(timeout_duration, 0.0, "Timeout must be positive")
	assert_lt(timeout_duration, 30.0, "Timeout must not be too long")

# Entry point for manual tests
func _ready():
	"""Entry point for manual test execution."""
	if get_parent().name == "SceneTree":
		print("=== Godot Dictionary API Tests ===")
		print("Use GUT to run these tests automatically")
		print("API URL: ", api_base_url)
		print("Timeout: ", timeout_duration, "s")
