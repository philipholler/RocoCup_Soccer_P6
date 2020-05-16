//This file was generated from (Academic) UPPAAL 4.1.20-stratego-6 (rev. 0DC1FC6317AF6369), October 2019

/*

*/
strategy safe = control: A[] not (final_stamina_interval < 2)

/*

*/
strategy opt_power = maxE(new_dash_power) [<=1000]: <> player.dash under safe

/*

*/
saveStrategy("/home/lockeyhannah/PycharmProjects/RocoCup_Soccer_P6/src/uppaal/outputdir/staminamodel/staminamodell6", opt_power)


