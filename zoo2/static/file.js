var copyMissingButton = document.getElementById('copy_missing');
copyMissingButton.hidden = true;
copyMissingButton.addEventListener('click', copyMissing);

var stringsTable = document.getElementById('translation_strings');
stringsTable.addEventListener('change', function(event) {
	checkStrings(event.target);
});
stringsTable.addEventListener('input', function(event) {
	checkStrings(event.target);
});

var keys = document.querySelectorAll('td.key');
for (var i = 0; i < keys.length; i++) {
	checkStrings(keys[i]);
}

function checkStrings(element) {
	var keyRow;
	if (element.localName == 'td' && element.classList.contains('key')) {
		keyRow = element.parentNode;
	} else if (element.localName == 'input') {
		keyRow = element.parentNode.parentNode.previousElementSibling;
	}

	var base = keyRow.querySelector('td.base');
	var valueRow = keyRow.nextElementSibling;
	var value = valueRow.querySelector('input[type="text"]');

	if (value.value.trim() === '') {
		keyRow.classList.add('rowmissing');
		valueRow.classList.add('rowmissing');
		copyMissingButton.hidden = false;
	} else {
		keyRow.classList.remove('rowmissing');
		valueRow.classList.remove('rowmissing');
		copyMissingButton.hidden = !document.querySelector('.rowmissing');

		if (value.value == base.textContent) {
			keyRow.classList.add('rowduplicate');
			valueRow.classList.add('rowduplicate');
		} else {
			keyRow.classList.remove('rowduplicate');
			valueRow.classList.remove('rowduplicate');
		}
	}
}

function copyMissing() {
	for (var i = 0; i < keys.length; i++) {
		var key = keys[i];
		var keyRow = key.parentNode;
		var base = keyRow.querySelector('td.base');
		var valueRow = keyRow.nextElementSibling;
		var value = valueRow.querySelector('input[type="text"]');

		if (value.value.trim() === '') {
			value.value = base.textContent;
			keyRow.classList.remove('rowmissing');
			valueRow.classList.remove('rowmissing');
		}
	}
	copyMissingButton.hidden = true;
}
