window.addEventListener("load", function () {
    let loader = document.getElementById("preloader");
    if (loader) {
        loader.style.display = "none";
    }
});

// Run when page loads
window.onload = function () {
    checkAuth();
};

// Owl Carousel inside document ready
$(document).ready(function () {
    $(".owl-carousel").owlCarousel({
        loop: true,
        margin: 10,
        nav: true,
        responsive: {
            0: {
                items: 1,
            },
            600: {
                items: 3,
            },
            1000: {
                items: 4,
            },
        },
    });
});


