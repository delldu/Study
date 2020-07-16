function ChoseFile(buttonName) {
	document.getElementById(buttonName).click();
}

function PreviewImage(file, canvasname) {
	if (file.files && file.files[0]) {
		var img = document.getElementById(canvasname);
		img.onload = function() {}
		var reader = new FileReader();
		reader.onload = function(evt) {
			img.src = evt.target.result;
		}
		reader.readAsDataURL(file.files[0]);
	}
}

