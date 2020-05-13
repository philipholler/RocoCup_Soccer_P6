//This file was generated from (Academic) UPPAAL 4.1.20-stratego-6 (rev. 0DC1FC6317AF6369), October 2019

/*

*/
strategy safe = control: A[] not (final_stamina_interval < 3 and player.dash)

/*

*/
strategy opt_power = maxE(new_dash_power) [<=100]: <> player.dash

/*

*/
saveStrategy("/home/lockeyhannah/PycharmProjects/RocoCup_Soccer_P6/src/uppaal/outputdir/staminamodel/staminamodell4", opt_power)


