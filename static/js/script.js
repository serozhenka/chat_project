function preloadCallback(src, elementId) {
  let img = document.getElementById(elementId)
  img.src = src
}

function preLoadImage(imgSrc, elementId) {
  let imagePreloader = new Image()
  imagePreloader.src = imgSrc

  if (imagePreloader.complete) {
    preloadCallback(imagePreloader.src, elementId)
    imagePreloader.onload = function(e) {}
  } else {
    imagePreloader.onload = function(e) {
      preloadCallback(imagePreloader.src, elementId)
      imagePreloader.onload = function(e) {}
    }
  }
}