/* When the user clicks on the button,
toggle between hiding and showing the dropdown content */
function toggle_content() {
  document.getElementById("notificationsDropdown").classList.toggle("show");
}

// Close the dropdown menu if the user clicks outside of it
window.onclick = function(event) {
  if (!event.target.matches('.clickable-dropbtn')) {
    let dropdowns = document.getElementsByClassName("clickable-dropdown-content");
    let i;
    for (i = 0; i < dropdowns.length; i++) {
      let openDropdown = dropdowns[i];
      if (openDropdown.classList.contains('show')) {
        openDropdown.classList.remove('show');
      }
    }
  }
}
