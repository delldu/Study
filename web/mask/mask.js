function ChoseFile(buttonName) {
	document.getElementById(buttonName).click();
}

function ReadImageData(img, fileobj) {
	// img --  image element
	img.onload = function() {}
	var reader = new FileReader();
	reader.onload = function(evt) {
		img.src = evt.target.result;
	}
	reader.readAsDataURL(fileobj);
}


function PreviewImage(file, canvasname) {
	if (file.files && file.files[0]) {
		var img = document.getElementById(canvasname);
		ReadImageData(img, file.files[0]);

		if (canvasname == "source_canvas") {
			var blend_fg = document.getElementById("blend_fg_canvas");
			ReadImageData(blend_fg, file.files[0]);
			// blend_fg.src = img.src;
		}

		if (canvasname == "mask_canvas") {
			var blend_bg = document.getElementById("blend_bg_canvas");
			blend_bg.style.backgroundImage = "url('" + file.files[0].name + "')";
		}
	}
}
