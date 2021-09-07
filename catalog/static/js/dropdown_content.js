
// Close the dropdown menu if the user clicks outside of it
window.onclick = function(event) {
  if (!event.target.matches('.clickable-dropbtn')) {
    let dropdowns = document.getElementsByClassName("clickable-dropdown-content");
    let i;
    for (i = 0; i < dropdowns.length; i++) {
      let openDropdown = dropdowns[i];
      if (openDropdown.classList.contains('show')) {
        openDropdown.classList.remove('show');
        let selector = document.getElementsByClassName("unread-notification");
        $(selector).css("font-weight", "normal");
        $(selector).css("color", "grey");
      }
    }
  }
}
