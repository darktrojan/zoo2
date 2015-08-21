var pluralForms = [
	['Any'],
	['1', 'Other'],
	['0, 1', 'Other'],
	['0', '1, 21, 31, 41, 51, 61\u2026', 'Other'],
	['1, 11', '2, 12', '3, 4, 5, 6, 7, 8, 9, 10\u2026', 'Other'],
	['1', '0, 2, 3, 4, 5, 6, 7, 8\u2026', 'Other'],
	['1, 21, 31, 41, 51, 61\u2026', '0, 10, 11, 12, 13, 14\u2026', 'Other'],
	['1, 21, 31, 41, 51, 61\u2026', '2, 3, 4, 22, 23, 24, 32\u2026', 'Other'],
	['1', '2, 3, 4', 'Other'],
	['1', '2, 3, 4, 22, 23, 24, 32\u2026', 'Other'],
	['1, 101, 201, 301, 401\u2026', '2, 102, 202, 302, 402,\u2026', '3, 4, 103, 104, 203, 204\u2026', 'Other'],
	['1', '2', '3, 4, 5, 6', '7, 8, 9, 10', 'Other'],
	['1', '2', '3, 4, 5, 6, 7, 8, 9, 10\u2026',
		'11, 12, 13, 14, 15, 16\u2026', '100, 101, 102, 200, 201\u2026', '0'],
	['1', '0, 2, 3, 4, 5, 6, 7, 8\u2026', '11, 12, 13, 14, 15, 16\u2026', 'Other'],
	['1, 11, 21, 31, 41, 51\u2026', '2, 12, 22, 32, 42, 52\u2026', 'Other'],
	['1, 21, 31, 41, 51, 61\u2026', 'Other'],
	['1', '21, 31, 41, 51, 61, 81\u2026', '2, 22, 32, 42, 52, 62\u2026', '3, 4, 9, 23, 24, 29, 33\u2026',
		'1000000, 2000000\u2026', 'Other']
];
var pluralNames = [
	'Asian', 'Germanic', 'French, Brazilian Portuguese', 'Latvian', 'Scottish Gaelic',
	'Romanian', 'Lithuanian', 'Belarusian, Bosnian, Croatian, Serbian, Russian, Ukrainian',
	'Slovak, Czech', 'Polish', 'Slovenian, Sorbian', 'Irish Gaelic', 'Arabic', 'Maltese',
	'Macedonian', 'Icelandic', 'Breton'
];
var pluralExampleValues = [
	[1], [1, 2], [1, 2], [0, 1, 2], [1, 2, 3, 20], [1, 2, 20], [1, 10, 2], [1, 2, 5],
	[1, 2, 5], [1, 2, 5], [1, 2, 3, 5], [1, 2, 3, 7, 11], [1, 2, 3, 11, 100, 0], [1, 2, 11, 20],
	[1, 2, 3], [1, 2], [1, 21, 2, 3, 1000000, 5]
];

var copyMissingButton = document.getElementById('copy_missing');
copyMissingButton.hidden = true;
copyMissingButton.addEventListener('click', copyMissing);

var stringsTable = document.getElementById('translation_strings');
stringsTable.addEventListener('change', function(event) {
	if (event.target.localName == 'input') {
		var value = event.target.value;
		value = value.trim().replace(/\.{3,}/g, '\u2026');
		event.target.value = value;
	} else if (event.target.localName == 'select') {
		var name = event.target.name.replace(/^locale_strings\[/, '').replace(/\]$/, '');
		var inputs = document.querySelectorAll('[data-plurals="' + name + '"] > input[type="text"]');
		for (var i = 0; i < inputs.length; i++) {
			updatePluralsUICell(inputs[i]);
		}
	}
	checkStrings(event.target);
	updateCounts();
});
stringsTable.addEventListener('input', function(event) {
	checkStrings(event.target);
	updateCounts();
	showExample(event.target);
});

(function() {
	var inputs = stringsTable.querySelectorAll('td.value > input[type="text"]');
	for (var i = 0; i < inputs.length; i++) {
		checkStrings(inputs[i]);
		showExample(inputs[i]);
		setupPluralsUI(inputs[i]);
	}
	for (var i = 0; i < inputs.length; i++) {
		// Loop twice, because otherwise things might not be ready yet.
		updatePluralsUICell(inputs[i]);
	}
	updateCounts();
})();

function checkStrings(element) {
	if (element.parentNode.classList.contains('plural_list')) {
		var cell = element.parentNode.parentNode;
		var input = cell.querySelector('input[type="text"]');
		var list_inputs = cell.querySelectorAll('div.plural_list > input');
		var values = [];
		for (var i = 0; i < list_inputs.length; i++) {
			values.push(list_inputs[i].value);
		}
		input.value = values.join(';');
		checkStrings(input);
		return;
	}

	var keyRow;
	if (element.localName == 'td' && element.classList.contains('key')) {
		keyRow = element.parentNode;
	} else if (element.localName == 'input' || element.localName == 'select') {
		keyRow = element.parentNode.parentNode.previousElementSibling;
	}

	var base = keyRow.querySelector('td.base');
	var valueRow = keyRow.nextElementSibling;
	var value = valueRow.querySelector('input[type="text"], select');

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
	var total = stringsTable.querySelectorAll('td.value').length;
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
	var inputs = stringsTable.querySelectorAll('td.value > input[type="text"]');
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

			updatePluralsUICell(value);
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

function setupPluralsUI(input) {
	var cell = input.parentNode;
	var pluralRule = cell.dataset.pluralRule;
	if (pluralRule != 'true') {
		return;
	}

	var select = document.createElement('select');
	select.name = input.name;
	for (var i = 0; i <= 16; i++) {
		var option = document.createElement('option');
		option.value = i;
		option.textContent = i + ' ' + pluralNames[i];
		select.appendChild(option);
	}
	select.value = input.value;
	cell.replaceChild(select, input);

	cell.appendChild(document.createTextNode('\u00A0'));

	var anchor = document.createElement('a');
	anchor.classList.add('small');
	anchor.href = 'https://developer.mozilla.org/docs/Mozilla/Localization/Localization_and_Plurals';
	anchor.target = '_new';
	anchor.textContent = 'Help with this';
	cell.appendChild(anchor);
}

function updatePluralsUICell(input) {
	var cell = input.parentNode;
	if (!cell) {
		return;
	}
	var plurals = cell.dataset.plurals;
	if (!plurals) {
		return;
	}

	var rule = document.querySelector('select[name="locale_strings[' + plurals + ']"]');
	if (!rule) {
		return;
	}

	var ruleValue = parseInt(rule.value, 10);
	var values = input.value.split(';');

	input.readOnly = true;
	while (input.nextElementSibling) {
		input.nextElementSibling.remove();
	}
	pluralForms[ruleValue].forEach(function(value, i) {
		var div = document.createElement('div');
		div.classList.add('plural_list');
		var label = document.createElement('label');
		label.textContent = value;
		div.appendChild(label);
		var list_input = document.createElement('input');
		list_input.type = 'text';
		list_input.value = values[i] || '';
		div.appendChild(list_input);
		cell.appendChild(div);

		// TODO examples with other placeholders
		var exampleValue = pluralExampleValues[ruleValue][i];
		var exampleDiv = document.createElement('div');
		exampleDiv.classList.add('example');
		exampleDiv.textContent = 'Example: ' + list_input.value.replace('%S', exampleValue);
		cell.appendChild(exampleDiv);

		list_input.dataset.exampleValue = exampleValue;
		list_input.addEventListener('input', function() {
			exampleDiv.textContent = 'Example: ' + this.value.replace('%S', this.dataset.exampleValue);
		});
	});
}
