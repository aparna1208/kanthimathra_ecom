document.addEventListener("DOMContentLoaded", function () {

    document.querySelectorAll(".wishlist-btn").forEach(button => {

        button.addEventListener("click", function () {

            const productId = this.dataset.product;
            const heart = this.querySelector(".heart-icon");

            fetch("/api/wishlist/toggle/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCookie("csrftoken"),
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                body: `product_id=${productId}`
            })
            .then(response => response.json())
            .then(data => {

                if (data.status === "added") {
                    heart.classList.remove("text-zinc-400");
                    heart.classList.add("text-brownMain");
                    heart.setAttribute("fill", "currentColor");
                } else {
                    heart.classList.remove("text-brownMain");
                    heart.classList.add("text-zinc-400");
                    heart.setAttribute("fill", "none");
                }

            });
        });

    });
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        document.cookie.split(";").forEach(cookie => {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            }
        });
    }
    return cookieValue;
}
