// Simple "Flipkart-like" left tab switching
  const tabs = document.querySelectorAll('.payTab');
  const panels = document.querySelectorAll('.payPanel');

  function activateTab(targetId){
    panels.forEach(p => p.classList.add('hidden'));
    const panel = document.getElementById(targetId);
    if (panel) panel.classList.remove('hidden');

    tabs.forEach(t => t.classList.remove('bg-white'));
    const active = [...tabs].find(t => t.dataset.target === targetId);
    if (active) active.classList.add('bg-white');
  }

  tabs.forEach(btn => {
    btn.addEventListener('click', () => activateTab(btn.dataset.target));
  });

  // Default active
  activateTab('tabUPI');





// Razorpay Integration
document.addEventListener("DOMContentLoaded", () => {

    const payButtons = document.querySelectorAll(".payNowBtn");

    payButtons.forEach(btn => {
        btn.addEventListener("click", () => {

            fetch("/razorpay/create/")
                .then(res => res.json())
                .then(data => {

                    if (data.error) {
                        alert("Cart empty");
                        return;
                    }

                    const options = {
                        key: data.key,
                        amount: data.amount,
                        currency: "INR",
                        name: "Kanthimandra",
                        description: "Order Payment",
                        order_id: data.order_id,

                        handler: function (response) {
                            fetch("/razorpay/verify/", {
                                method: "POST",
                                headers: {
                                    "Content-Type": "application/x-www-form-urlencoded",
                                    "X-CSRFToken": getCookie("csrftoken")
                                },
                                body: new URLSearchParams(response)
                            })
                            .then(res => res.json())
                            .then(result => {
                                if (result.status === "success") {
                                    window.location.href = "/order-success/";
                                } else {
                                    alert("Payment verification failed");
                                }
                            });
                        },

                        theme: {
                            color: "#6B3F2A"
                        }
                    };

                    const rzp = new Razorpay(options);
                    rzp.open();
                });
        });
    });
});

// CSRF helper
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
