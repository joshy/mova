$(function () {
  console.log('ready')
  var job_id = $('#loading').data("job-id")

  if (job_id == "None") {
    document.getElementById("loading").classList.add("dn");
    document.getElementById("papaya_div").classList.remove("dn");
  }

  var params = []
  params["images"] = [$("#papaya_div").data("images")];
  params["fullScreenPadding"] = false;
  params["kiosMode"] = false;
  params["padAllImages"] = false;
  params["loadingComplete"] = function () {
    console.log("loaded")
  }
  if ($("papaya_div").data("cr-modality")) {
    params["orthogonal"] = false;
  }
  papaya.Container.addViewer("papaya_div", params)
  papaya.Container.startPapaya();
  papaya.Container.resetViewer(0, params);
});