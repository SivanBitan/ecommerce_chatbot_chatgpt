function getBotResponse() {
    // get the response from the bot and post it
    var rawText = $("#textInput").val();
    var userHtml = '<p class="userText"><span>' + rawText + "</span></p>";
    $("#textInput").val("");
    $("#chatbox").append(userHtml);
    document.getElementById("userInput").scrollIntoView({ block: "start", behavior: "smooth" });
    $.get("/get", { msg: rawText }).done(function (data) {
        var botHtml = '<p class="botText"><span>' + data + "</span></p>";
        $("#chatbox").append(botHtml);
        document.getElementById("userInput").scrollIntoView({ block: "start", behavior: "smooth" });
// This is the form version's if
//        // Check if the response contains the specific message for contact details
//        if (data.includes("Please provide your contact details below.")) {
//            $("#contactInput").show();
//            document.getElementById("contactInput").scrollIntoView({ block: "end", behavior: "smooth" });
//        }
    }).fail(function() {
        // Handle errors in communication with the server
        console.error("Error: Unable to get response from server");
    });
}

$("#textInput").keypress(function (e) {
    console.log("Key pressed: " + e.which);  // Debugging statement to monitor the pressed button
    if (e.which == 13) {
        getBotResponse(); // call "/get" and show results
    }
});
//
//Originally I opened a form so that the user can input data, but considering the assignment
//I figured having the chat doing it instead is more suiting to the instructions
//
//$("#contact-form").on("submit", function(e) {
//    e.preventDefault();
//    var fullName = $("#full_name").val();
//    var email = $("#email").val();
//    var phoneNumber = $("#phone_number").val();
//
//    $.post("/save_contact_info", {
//        full_name: fullName,
//        email: email,
//        phone_number: phoneNumber
//    }).done(function(data) {
//        var botHtml = '<p class="botText"><span>' + data + "</span></p>";
//        $("#chatbox").append(botHtml);
//        document.getElementById("userInput").scrollIntoView({ block: "start", behavior: "smooth" });
//        $("#contactInput").hide();  // Hide the contact form after submission
//        $("#contact-form")[0].reset();  // Reset the form fields
//    }).fail(function() {
//        console.error("Error: Unable to save contact info");
//    });
//});
