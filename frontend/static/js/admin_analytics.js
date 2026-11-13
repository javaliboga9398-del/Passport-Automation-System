/* =========================================================
   Admin Operational Analytics
   Passport Automation System
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    const analyticsSection =
        document.querySelector(".analytics-section");

    if (!analyticsSection) {
        return;
    }

    /*
     * Animate progress bars after the dashboard loads.
     */
    const progressBars =
        analyticsSection.querySelectorAll(
            ".analytics-progress-bar"
        );

    progressBars.forEach(function (bar) {

        const percentage =
            parseFloat(bar.dataset.percentage || "0");

        const safePercentage =
            Math.min(Math.max(percentage, 0), 100);

        setTimeout(function () {
            bar.style.width = safePercentage + "%";
        }, 150);
    });


    /*
     * Add a small visual interaction to analytics cards.
     */
    const analyticsCards =
        analyticsSection.querySelectorAll(
            ".analytics-card"
        );

    analyticsCards.forEach(function (card) {

        card.addEventListener("mouseenter", function () {
            card.setAttribute("data-hovered", "true");
        });

        card.addEventListener("mouseleave", function () {
            card.removeAttribute("data-hovered");
        });

    });


    /*
     * Display a useful browser-console message
     * for developers/administrators.
     */
    const totalApplications =
        analyticsSection.dataset.totalApplications || "0";

    const pendingApplications =
        analyticsSection.dataset.pendingApplications || "0";

    console.info(
        "Passport Authority Analytics loaded:",
        {
            totalApplications: totalApplications,
            pendingApplications: pendingApplications
        }
    );

});
