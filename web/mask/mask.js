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
		var reader = new FileReader();
		reader.onload = function(evt) {
			img.src = evt.target.result;
		}
		reader.readAsDataURL(file.files[0]);
	}
}


function UpdateBlendCanvas() {
	var source_canvas = document.getElementById("source_canvas");
	var mask_canvas = document.getElementById("mask_canvas");
	var blend_canvas = document.getElementById("blend_canvas");

	// Make sure blend canvas is big enough !
	blend_canvas.height = Math.max(source_canvas.height, mask_canvas.height);
	blend_canvas.width = Math.max(source_canvas.width, mask_canvas.width);

	if (source_canvas.src.length > 64 && mask_canvas.src.length > 64) {
		// Empty image object length is 42, base64 length is at least 64 !
		var need_blend_update = 0;
		var ctx = blend_canvas.getContext('2d');

		ctx.drawImage(mask_canvas, 0, 0, mask_canvas.width, mask_canvas.height);
		var maskimg = ctx.getImageData(0, 0, mask_canvas.width, mask_canvas.height);

		ctx.drawImage(source_canvas, 0, 0, source_canvas.width, source_canvas.height);
		var sourceimg = ctx.getImageData(0, 0, source_canvas.width, source_canvas.height);

		for (var i = 0 , len = Math.min(maskimg.data.length, sourceimg.data.length) ; i < len ; i += 4 ) {
			if (maskimg.data[i] > 128 && maskimg.data[i + 1] > 128 && maskimg.data[i + 2] > 128) {
				sourceimg.data[i] = maskimg.data[i];
				sourceimg.data[i + 1] = maskimg.data[i + 1];
				sourceimg.data[i + 2] = maskimg.data[i + 2];
				sourceimg.data[i + 3] = maskimg.data[i + 3];
				need_blend_update = 1;
			}
		}
		if (need_blend_update) {
			ctx.putImageData(sourceimg, 0 , 0);
		}
	}
}