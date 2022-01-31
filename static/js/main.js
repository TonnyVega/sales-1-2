main
$(document).ready( function () {
    $('#example').DataTable();
} );

$(document).ready(function () {
    $('#sidebarCollapse').on('click', function () {
        $('#sidebar').toggleClass('active');
    });
});

function deleteNote(noteId) {
    fetch('/delete-note', {
        method: 'POST',
        body: JSON.stringify({noteId})
    }).then((_res) => {
        window.location.href ="/dashboard";
    });
}