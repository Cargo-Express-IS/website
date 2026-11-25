// Track & trace: read an 11-digit AWB, pick the airline from its 3-digit prefix,
// open that airline's tracking page and copy the AWB so it can be pasted there.
// Prefixes come from content/site.json (only confirmed ones are included).
(function () {
  var form = document.getElementById("track-form");
  var input = document.getElementById("awb");
  var msg = document.getElementById("track-msg");
  var data = document.getElementById("awb-prefixes");
  if (!form || !input || !msg || !data) return;

  var prefixes = {};
  try { prefixes = JSON.parse(data.textContent) || {}; } catch (e) { /* keep empty */ }

  function say(key, values, isError) {
    var text = form.getAttribute("data-msg-" + key) || "";
    Object.keys(values || {}).forEach(function (k) {
      text = text.split("{" + k + "}").join(values[k]);
    });
    msg.textContent = text;
    msg.classList.toggle("is-error", !!isError);
  }

  function formatAwb(digits) {
    return digits.slice(0, 3) + "-" + digits.slice(3, 7) + " " + digits.slice(7);
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    var digits = (input.value || "").replace(/\D/g, "");

    if (digits.length !== 11) {
      say("invalid", {}, true);
      input.focus();
      return;
    }

    var prefix = digits.slice(0, 3);
    var airline = prefixes[prefix];
    if (!airline) {
      say("unknown", { prefix: prefix }, true);
      return;
    }

    var awb = formatAwb(digits);
    // Open first, while the click still counts as a user action (popup blockers).
    window.open(airline.url, "_blank", "noopener");

    var values = { airline: airline.name, awb: awb };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(digits).then(
        function () { say("found", values, false); },
        function () { say("found-nocopy", values, false); }
      );
    } else {
      say("found-nocopy", values, false);
    }
  });
})();
