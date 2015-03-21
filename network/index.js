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
      console.log(json.status)
      var temperature_info_zone = $('.temperatures')
      temperature_info_zone.html('')
      for(var key in json.status){
        console.log( key)
        if( key.includes('temperature_') ){
          temperature_info_zone.append('<div>' + key + ': ' + json.status[key] + '</div>')
        }
      } 
    }
  })
}
