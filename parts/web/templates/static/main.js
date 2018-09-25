var driveHandler = new function() {
    //functions used to drive the vehicle.

    var state = { 'vehicle_running': false,
                  'recording': false,
                  'driveMode': "user",
                  }

    var driveURL = ""

    this.load = function() {
      driveURL = '/status'
      setInterval(proc_updates, 200)      
      setBindings()
    };


    var setBindings = function() {
      console.log("set bindings")
      $(document).keydown(function(e) {
          if(e.which == 32) { toggleBrake() }  // 'space'  brake
          if(e.which == 82) { toggleRecording() }  // 'r'  toggle recording
          if(e.which == 65) { updateDriveMode('auto') } // 'a' turn on auto mode
          if(e.which == 68) { updateDriveMode('user') } // 'd' turn on manual mode
          if(e.which == 83) { updateDriveMode('auto_angle') } // 'a' turn on auto mode
      });

      $('#mode_select').on('change', function () {
        updateDriveMode($(this).val());
      });

      $('#record_button').click(function () {
        toggleRecording();
      });

      $('#brake_button').click(function() {
        toggleBrake();
      });
    };

    var proc_updates = function() {
      $.get( "/updates", function( data ) {
        $( "#updates-results" ).text(JSON.stringify(data, null, 1));
      }, "json");
    }

    var updateUI = function() {
      $('#mode_select').val(state.driveMode);

      if (state.recording) {
        $('#record_button')
          .html('Stop Recording (r)')
          .removeClass('btn-info')
          .addClass('btn-warning').end()
      } else {
        $('#record_button')
          .html('Start Recording (r)')
          .removeClass('btn-warning')
          .addClass('btn-info').end()
      }

      if (!state.vehicle_running) {
        $('#brake_button')
          .html('Start Vehicle')
          .removeClass('btn-danger')
          .addClass('btn-success').end()
      } else {
        $('#brake_button')
          .html('Stop Vehicle')
          .removeClass('btn-success')
          .addClass('btn-danger').end()
      }

    };

    var postDrive = function() {
      //Send angle and throttle values
      data = JSON.stringify({ 'vehicle_running': state.vehicle_running,
                              'drive_mode': state.driveMode,
                              'recording': state.recording})
      console.log(data)
      $.post(driveURL, data)
      updateUI()
  };

    var updateDriveMode = function(mode){
      state.driveMode = mode;
      postDrive()
    };

    var toggleRecording = function(){
      state.recording = !state.recording
      postDrive()
    };

    var toggleBrake = function(){
      state.vehicle_running = !state.vehicle_running;

      if (!state.vehicle_running) {
        state.recording = false
        state.driveMode = 'user';
      }
      postDrive()
    };

}();


