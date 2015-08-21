var copyMissingButton = document.getElementById('copy_missing');
copyMissingButton.hidden = true;
copyMissingButton.addEventListener('click', copyMissing);

var stringsTable = document.getElementById('translation_strings');
stringsTable.addEventListener('change', function(event) {
	var value = event.target.value;
	value = value.trim().replace(/\.{3,}/g, '\u2026');
	event.target.value = value;
	checkStrings(event.target);
	updateCounts();
});
stringsTable.addEventListener('input', function(event) {
	checkStrings(event.target);
	updateCounts();
	showExample(event.target);
});

var inputs = document.querySelectorAll('table#translation_strings input[type="text"]');
for (var i = 0; i < inputs.length; i++) {
	checkStrings(inputs[i]);
	showExample(inputs[i]);
	setupPluralUI(inputs[i]);
}
updateCounts();

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
		copyMissingButton.hidden = false;
	} else {
		keyRow.classList.remove('rowmissing');
		copyMissingButton.hidden = !document.querySelector('.rowmissing');

		if (value.value == base.textContent) {
			keyRow.classList.add('rowduplicate');
		} else {
			keyRow.classList.remove('rowduplicate');
		}
	}
}

function updateCounts() {
	var total = inputs.length;
	var duplicate = document.querySelectorAll('.rowduplicate').length;
	var missing = document.querySelectorAll('.rowmissing').length;
	var translated = total - duplicate - missing;

	document.querySelector('#status > .translated').style.width = (translated / total * 200) + 'px';
	document.querySelector('#status > .duplicate').style.width = (duplicate / total * 200) + 'px';
	document.querySelector('#status > .missing').style.width = (missing / total * 200) + 'px';

	var list = document.querySelector('#status > ul');
	while (list.lastChild) {
		list.lastChild.remove();
	}
	if (translated) {
		var item = document.createElement('li');
		item.appendChild(document.createTextNode(translated + ' translated'));
		list.appendChild(item);
	}
	if (duplicate) {
		var item = document.createElement('li');
		item.appendChild(document.createTextNode(duplicate + ' matching'));
		list.appendChild(item);
	}
	if (missing) {
		var item = document.createElement('li');
		item.appendChild(document.createTextNode(missing + ' missing'));
		list.appendChild(item);
	}
}

function copyMissing() {
	for (var i = 0; i < inputs.length; i++) {
		var value = inputs[i];
		if (value.value.trim() === '') {
			var valueRow = value.parentNode.parentNode;
			var keyRow = valueRow.previousElementSibling;
			var base = keyRow.querySelector('td.base');

			value.value = base.textContent;
			showExample(value);
			keyRow.classList.remove('rowmissing');
			keyRow.classList.add('rowduplicate');
		}
	}
	copyMissingButton.hidden = true;

	updateCounts();
}

function showExample(input) {
	var cell = input.parentNode;
	var exampleData = cell.dataset.exampleData;
	if (!exampleData) {
		return;
	}

	var example = cell.querySelector('div.example');
	if (!example) {
		example = document.createElement('div');
		example.classList.add('example');
		cell.appendChild(example);
	}
	var value = input.value;
	exampleData.split('&').forEach(function(part) {
		var parts = part.split('=', 2);
		var search = decodeURIComponent(parts[0]).trim();
		var replacement = decodeURIComponent(parts[1]).trim().replace(/\+/g, ' ');
		while (value.indexOf(search) >= 0) {
			value = value.replace(search, replacement);
		}
	});
	example.textContent = 'Example: ' + value;
}

function setupPluralUI(input) {
	var cell = input.parentNode;
	var pluralRule = cell.dataset.pluralRule;
	if (pluralRule != 'true') {
		return;
	}

	input.type = 'hidden';
	var select = document.createElement('select');
	for (var i = 0; i <= 16; i++) {
		var option = document.createElement('option');
		option.label = option.textContent = i;
		select.appendChild(option);
	}
	select.value = input.value;
	cell.appendChild(select);

	cell.appendChild(document.createTextNode('\u00A0'));

	var anchor = document.createElement('a');
	anchor.classList.add('small');
	anchor.href = 'https://developer.mozilla.org/docs/Mozilla/Localization/Localization_and_Plurals';
	anchor.target = '_new';
	anchor.textContent = 'Help with this';
	cell.appendChild(anchor);
}
