//# SPDX-License-Identifier: GPL-3.0-or-later

/*
Wait for document content to load, before attaching
event handlers.
*/
document.addEventListener('DOMContentLoaded', function() {

    // Add handler for dismissing wmf account link request.
    const removable_elements = document.getElementsByClassName('cdx-message__dismiss-button');
    for (element of removable_elements) {
        element.onclick = function(event){
            //p = event.srcElement.parentElement.parentElement.parentElement.parentElement.parentElement;
            p = event.srcElement.closest(".message-box")
            p_name = p.getAttribute("name");
            p.remove()
            if(document.cookie){
                document.cookie = p_name + "=no; " + document.cookie;
            } else {
                document.cookie(p_name + "=no; path=/; SameSite=Strict");
            }
        };
    }

    /* navigation, handle responsive menu */
    if ( document.getElementsByClassName('toggle').length > 0 ){
    document.getElementsByClassName('toggle')[0].addEventListener("click", (event) => {
        var items = document.getElementsByClassName("item");
        for (var item of items) {
            if ( item.classList.contains('active') ){
                item.classList.remove('active')
            } else {
                item.classList.add('active');
            }
        }
    });
    };

    // Allow users to hidde the menu by clicking the hamburger menu.
    menu = document.getElementsByClassName('menu')
    if(menu.length > 0){
        menu[0].addEventListener("click", (event) => {
            var dropdown = document.getElementById("nav_menu");
            if (dropdown.style.display === "") {
                dropdown.style.display = "none";
            } else {
                dropdown.style.display = "";
                dropdown.style.visibility = "visible";
            }
        });

        // Ensure that mouseover still triggers the menu after earlier dismissal.
        menu[0].addEventListener("mouseover", (event) => {
            var dropdown = document.getElementById("nav_menu");
            dropdown.style.display = "";
            dropdown.style.visibility = "visible";
        });
    }

}, false);

function toggle_ssh_key_display(element){
    // Swap display style for truncated and full SSH keys.
    short = element.parentElement.parentElement.firstChild;
    long = short.nextElementSibling;
    long.style.display = [short.style.display, short.style.display = long.style.display][0]

    // Swap text for the trigger element for hide/show of untruncated SSH key.
    element.text = [element.dataset.textSwap, element.dataset.textSwap = element.text][0]
}