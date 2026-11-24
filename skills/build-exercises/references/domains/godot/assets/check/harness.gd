extends SceneTree
## The harness every Godot Exercise check shares. check/check.gd extends it and writes only that Exercise's lines,
## in run(). check.sh runs it as:
##   godot --headless --no-header --fixed-fps 60 --path <exercise> -s check/check.gd
## Leave this file as it is: the Exercise check relies on it being the one it shipped with.

## Exit codes check.sh maps to the Exercise check's 0, 1 and 2. They keep clear of 0 to 2 because Godot itself
## exits 1 when check/check.gd doesn't parse.
const PASSED := 10
const FAILED := 11
const CRASHED := 12

## The guard line the harness prints after run()'s lines. It fails on any runtime error outside check/.
const ERRORS_LINE := "No script errors."

## How many distinct errors the guard line names before it summarizes the rest.
const ERRORS_SHOWN := 3

## Seconds of game time run() may take before the Exercise check counts as crashed, such as when it awaits a
## signal that never comes. A check that needs longer sets it in _init().
var time_limit := 60.0

var _catcher := Catcher.new()
var _automated := 0
var _failed := 0
var _self_checks: Array[String] = []
var _elapsed := 0.0
var _done := false


## Collects every error the engine reports, from any thread. Those raised in check/ are the Exercise check's own;
## the rest, the learner's.
class Catcher extends Logger:
	var _mutex := Mutex.new()
	var _check: Array[String] = []
	var _learner: Array[String] = []  # each distinct error, in the order first seen
	var _counts := {}

	func _log_error(_function: String, file: String, line: int, code: String, rationale: String, _editor_notify: bool, error_type: int, script_backtrace: Array[ScriptBacktrace]) -> void:
		if error_type == ERROR_TYPE_WARNING:
			return
		# An engine error, such as reading an empty array, names its C++ source. It's shown at the script line that
		# caused it instead: the first frame of its GDScript backtrace outside check/, or else the top frame. Which
		# side it counts against still follows the reported file.
		var at := "%s:%d" % [file, line]
		if not file.begins_with("res://"):
			for backtrace in script_backtrace:
				if backtrace.get_frame_count() > 0:
					at = _script_line(backtrace)
					break
		var what := "%s %s" % [at, (rationale if rationale != "" else code).strip_edges()]
		_mutex.lock()
		if file.begins_with("res://check/"):
			_check.append(what)
		elif _counts.has(what):
			_counts[what] += 1
		else:
			_counts[what] = 1
			_learner.append(what)
		_mutex.unlock()

	func _log_message(_message: String, _error: bool) -> void:
		pass

	## "file:line" of the backtrace's first frame outside check/, or of its top frame when every frame is in check/.
	static func _script_line(backtrace: ScriptBacktrace) -> String:
		var frame := 0
		for i in backtrace.get_frame_count():
			if not backtrace.get_frame_file(i).begins_with("res://check/"):
				frame = i
				break
		return "%s:%d" % [backtrace.get_frame_file(frame), backtrace.get_frame_line(frame)]

	func check_errors() -> Array[String]:
		_mutex.lock()
		var out := _check.duplicate()
		_mutex.unlock()
		return out

	## The learner's errors as the guard line measures them: how many, then the first few with their counts.
	func learner_errors() -> Array:
		_mutex.lock()
		var out := []
		for what in _learner:
			out.append([what, _counts[what]])
		_mutex.unlock()
		return out


## Override in check/check.gd: drive the learner's project and call expect() once per automated line, and
## self_check() once per Self-check bullet, in the order "Done when" lists them.
func run() -> void:
	pass


## Prints one automated line: PASS or FAIL, its text, and the measured value in parentheses. Returns ok, so a
## later line can depend on it.
func expect(ok: bool, text: String, measured: String) -> bool:
	_automated += 1
	if not ok:
		_failed += 1
	print("%s %s (%s)" % ["PASS" if ok else "FAIL", text, measured.replace("\n", " ")])
	return ok


## Records a Self-check bullet. The harness prints every one last, under CHECK YOURSELF, outside the exit code.
func self_check(text: String) -> void:
	_self_checks.append(text)


## Waits until n more physics ticks, 1/60 s each, have run every _physics_process. physics_frame fires before a
## tick's _physics_process, so the last tick is let finish by waiting for the process frame that follows it.
func ticks(n: int) -> void:
	if n <= 0:
		return
	for i in n:
		await physics_frame
	await process_frame


## Waits n process frames.
func frames(n: int) -> void:
	for i in n:
		await process_frame


func _initialize() -> void:
	OS.add_logger(_catcher)
	_main()


func _main() -> void:
	await run()
	_finish()


func _process(delta: float) -> bool:
	if _done:
		return false
	_elapsed += delta
	if not _catcher.check_errors().is_empty():
		_stop()
	elif _elapsed > time_limit:
		_done = true
		printerr("The Exercise check didn't finish within %s s of game time." % time_limit)
		quit(CRASHED)
	return false


func _finish() -> void:
	if _done:
		return
	if not _catcher.check_errors().is_empty():
		_stop()
		return
	_report()


## Prints the guard line, the summary and the Self-check bullets, then quits with the verdict.
func _report() -> void:
	_done = true
	var errors := _catcher.learner_errors()
	expect(errors.is_empty(), ERRORS_LINE, _describe(errors))
	if _failed == 0:
		print("All %d lines passed." % _automated)
	else:
		print("%d of %d lines failed." % [_failed, _automated])
	if not _self_checks.is_empty():
		print("CHECK YOURSELF")
		for text in _self_checks:
			print("- " + text)
	quit(FAILED if _failed > 0 else PASSED)


## The Exercise check's own code raised an error. When the learner's code had already raised one, that's the likely
## cause, such as a script that didn't parse leaving a node without its methods, so the guard line fails and the
## verdict stands. Otherwise the Exercise check crashed.
func _stop() -> void:
	if not _catcher.learner_errors().is_empty():
		print("Your code's errors stopped the Exercise check before every line ran.")
		_report()
		return
	_done = true
	printerr("The Exercise check crashed in its own code:")
	for what in _catcher.check_errors():
		printerr("  " + what)
	quit(CRASHED)


func _describe(errors: Array) -> String:
	if errors.is_empty():
		return "0 errors"
	var shown := []
	for pair in errors.slice(0, ERRORS_SHOWN):
		shown.append(pair[0] + ("" if pair[1] == 1 else " (x%d)" % pair[1]))
	var more := errors.size() - ERRORS_SHOWN
	return "%d error%s: %s%s" % [errors.size(), "" if errors.size() == 1 else "s", "; ".join(shown), "; and %d more" % more if more > 0 else ""]
