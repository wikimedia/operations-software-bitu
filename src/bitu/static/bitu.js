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
            document.getElementsByClassName('cdx-message')[0].remove()
            document.cookie = "wmf_link=no; path=/; SameSite=Strict";
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
}, false);

function toggle_ssh_key_display(element){
    // Swap display style for truncated and full SSH keys.
    short = element.parentElement.parentElement.firstChild;
    long = short.nextElementSibling;
    long.style.display = [short.style.display, short.style.display = long.style.display][0]

    // Swap text for the trigger element for hide/show of untruncated SSH key.
    element.text = [element.dataset.textSwap, element.dataset.textSwap = element.text][0]
}