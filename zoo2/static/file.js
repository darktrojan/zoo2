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
});

var keys = document.querySelectorAll('td.key');
for (var i = 0; i < keys.length; i++) {
	checkStrings(keys[i]);
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
	var total = keys.length;
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
	for (var i = 0; i < keys.length; i++) {
		var key = keys[i];
		var keyRow = key.parentNode;
		var base = keyRow.querySelector('td.base');
		var valueRow = keyRow.nextElementSibling;
		var value = valueRow.querySelector('input[type="text"]');

		if (value.value.trim() === '') {
			value.value = base.textContent;
			keyRow.classList.remove('rowmissing');
			keyRow.classList.add('rowduplicate');
		}
	}
	copyMissingButton.hidden = true;

	updateCounts();
}
