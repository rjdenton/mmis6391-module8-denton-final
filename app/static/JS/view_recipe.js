document.addEventListener("DOMContentLoaded", () => {
    const collapsibles = document.querySelectorAll(".collapsible");
    console.log("Collapsible buttons found:", collapsibles.length); // Log number of buttons

    collapsibles.forEach((collapsible, index) => {
        console.log(`Attaching event to button ${index + 1}`);
        collapsible.addEventListener("click", function () {
            console.log("Button clicked"); // Log when the button is clicked
            this.classList.toggle("active");
            const content = this.nextElementSibling;
            if (content.style.display === "block") {
                content.style.display = "none";
            } else {
                content.style.display = "block";
            }
        });
    });
});
