$(function(){
  reload_temperature()
})

$(document).on('click', '.air-conditioner-switch', function(){
  $.get('handler/touch', function(data){
    reload_temperature()
    console.log('touched')
  })
})

function reload_temperature() {
  $.ajax({
    type: 'get',
    url: 'handler',
    dataType: 'json',
    success: function(json) {
      console.log(json)
      console.log(json.temperatures)
      var temperature_info_zone = $('.temperatures')
      temperature_info_zone.html('')
      for(var key in json.temperatures){
        if(json.temperatures[key] != ''){
          temperature_info_zone.append('<div>' + key + ': ' + json.temperatures[key] + '</div>')
        }
      } 
    }
  })
}
