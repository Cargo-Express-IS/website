// Quote form: build a clear email subject from what the visitor typed, e.g.
// "Quote request: Acme ehf. – KEF → MAD (AOG / urgent)".
// Netlify uses the hidden "subject" field as the notification email's subject.
(function () {
  var form = document.getElementById("quote-form");
  var subject = document.getElementById("q-subject");
  if (!form || !subject) return;

  function value(name) {
    var el = form.elements[name];
    return el && el.value ? el.value.trim() : "";
  }

  form.addEventListener("submit", function () {
    var company = value("Company") || "unknown company";
    var from = (value("From") || "KEF").split(/[\s–-]/)[0];
    var to = value("To") || "?";
    var flags = [];
    if (form.elements["AOG / urgent"] && form.elements["AOG / urgent"].checked) flags.push("AOG / urgent");
    if (form.elements["Dangerous goods"] && form.elements["Dangerous goods"].checked) flags.push("DG");
    if (form.elements["Temperature-controlled"] && form.elements["Temperature-controlled"].checked) flags.push("temp-controlled");
    subject.value = "Quote request: " + company + " – " + from + " → " + to +
      (flags.length ? " (" + flags.join(", ") + ")" : "");
  });
})();
