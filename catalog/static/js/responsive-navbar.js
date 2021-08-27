function responsive_navbar() {
  let x = document.getElementById("mainNavbar");
  if (x.className === "navbar") {
    x.className += " responsive";
  } else {
    x.className = "navbar";
  }
}