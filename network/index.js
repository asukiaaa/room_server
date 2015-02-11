$(document).on('click', '.air-conditioner-switch', function(){
  reload_temperature()
  $.get('handler/touch', function(data){
    console.log('get', data)
  })
})

function reload_temperature() {
  $.ajax({
    type: 'get',
    url: 'handler',
    dataType: 'json',
    success: function(json) {
      console.log(json)
      $('#tempertures').html(json)
    }
  })
}
