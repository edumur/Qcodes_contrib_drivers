# This Python file uses the following encoding: utf-8
import warnings

from qcodes import Instrument, VisaInstrument
from qcodes.instrument.channel import InstrumentChannel
from qcodes.utils.validators import Numbers, Enum
from qcodes.utils.helpers import create_on_off_val_mapping


class HS900Channel(InstrumentChannel):
    """
    Class to hold the Holzworth channels, i.e.
    CH1, CH2, ...
    """

    def __init__(self, parent: Instrument, name: str, channel: str) -> None:
        """
        Args:
            parent: The Instrument instance to which the channel is
                to be attached.
            name: The 'colloquial' name of the channel
            channel: The name used by the Holzworth, i.e. either
                     'CH1' or 'CH2'
        """

        super().__init__(parent, name)

        self.channel = channel

        self._min_f = self._parse_f_unit(
                      self.ask_raw(':{}:Freq:MIN?'.format(channel)))
        self._max_f = self._parse_f_unit(
                      self.ask_raw(':{}:Freq:MAX?'.format(channel)))
        self._min_pwr = self._parse_pwr_unit(
                        self.ask_raw(':{}:PWR:MIN?'.format(channel)))
        self._max_pwr = self._parse_pwr_unit(
                        self.ask_raw(':{}:PWR:MAX?'.format(channel)))
        self._min_phase = self._parse_phase_unit(
                          self.ask_raw(':{}:PHASE:MIN?'.format(channel)))
        self._max_phase = self._parse_phase_unit(
                          self.ask_raw(':{}:PHASE:MAX?'.format(channel)))

        self.add_parameter(name='state',
                           label='State',
                           get_parser=str,
                           get_cmd=':{}:PWR:RF?'.format(self.channel),
                           set_cmd=self._set_state,
                           val_mapping=create_on_off_val_mapping(on_val='ON',
                                                                 off_val='OFF'))

        self.add_parameter(name='power',
                           label='Power',
                           get_parser=float,
                           get_cmd=':{}:PWR?'.format(self.channel),
                           set_cmd= self._set_pwr,
                           unit='dBm',
                           vals=Numbers(min_value=self._min_pwr,
                                        max_value=self._max_pwr))

        self.add_parameter(name='frequency',
                           label='Frequency',
                           get_parser=float,
                           get_cmd=self._get_f,
                           set_cmd= self._set_f,
                           unit='Hz',
                           vals=Numbers(min_value=self._min_f,
                                        max_value=self._max_f))

        self.add_parameter(name='phase',
                           label='Phase',
                           get_parser=float,
                           get_cmd=':{}:PHASE?'.format(self.channel),
                           set_cmd= self._set_phase,
                           unit='deg',
                           vals=Numbers(min_value=self._min_phase,
                                        max_value=self._max_phase))

        self.add_parameter(name='temp',
                           label='Temperature',
                           get_parser=str,
                           get_cmd=self._get_temp,
                           unit='C')

    def _parse_f_unit(self, raw_str:str) -> float:
        """
        Function that converts strings consisting of a number and a unit into 
        frequencies in Hz and returing it as a float:

        Args:
            raw_str: String of the form '100 MHz'
        """
        f, unit = raw_str.split(' ')
        unit_dict = {
            'GHz': 1e9,
            'MHz': 1e6,
            'kHz': 1e3
        }
        if unit not in unit_dict.keys():
            raise RuntimeError('{} is not in {}. Cannot parse {}.'
                               .format(unit, unit_dict.keys(), unit))
        frequency = float(f) * unit_dict[unit]
        return frequency


    def _parse_pwr_unit(self, raw_str:str) -> float:
        """
        Function that converts strings consisting of a number only or 
        a number plus a unit dBm into a float in dBm:

        Args:
            raw_str: String of the form '-10' or '-10 dBm'
        """
        try:
            power = float(raw_str)
        except:
            pwr, unit = raw_str.split(' ')
            power = float(pwr)
        return power

    def _parse_phase_unit(self, raw_str:str) -> float:
        """
        Function that converts strings consisting of a number only or
        a number plus a unit deg into a float in deg:

        Args:
            raw_str: String of the form '90' or '90deg'
        """
        try:
            phase = float(raw_str)
        except:
            phase = float(raw_str[:-3])
        return phase

    def _set_state(self, st:{'ON','OFF'}) -> None:
        """
        Function that turns the channel on or off

        Args:
            st (str): accepts as argument 'ON' or 'OFF', only in CAPITAL letters

        Raises:
            RuntimeError: Function compares reply from instrument and raises
            RuntimeError if state setting was not performed sucessfully
        """
        write_str = ':{}:PWR:RF:'.format(self.channel) + str(st)
        read_str = self.ask(write_str)
        if read_str != 'RF POWER '+str(st):
            raise RuntimeError(
                         '{} is not \'State Set\'. Setting state did not work'
                         .format(read_str))

    def _get_f(self) -> float:
        """
        Getting the fundamental frequency from the RF source channel
        in Hz. Instrument gives frequency as a string in the format
        '800.0 MHz'.

        Returns:
            float: frequency in Hz, e.g. 0.8e9
        """
        raw_str = self.ask(':{}:FREQ?'.format(self.channel))
        return self._parse_f_unit(raw_str)

    def _set_f(self, f:float) -> None:
        """Function that sets the frequency of a channel.

        Args:
            f (float): RF source channel fundamental frequency in Hz

        Raises:
            RuntimeError: Instrument tells us if frequency has been set correctly.
            Otherwise RuntimeError.
        """
        write_str = ':{}:FREQ:'.format(self.channel) + str(f/1e9) + 'GHz'
        read_str = self.ask(write_str)
        if read_str != 'Frequency Set':
            raise RuntimeError(
                 '{} is not \'Frequency Set\'. Setting frequency did not work'
                 .format(read_str))

    def _set_pwr(self, pwr:float) -> None:
        """Setting the power of the RF source channel in dBm.

        Args:
            pwr (float): power in dBm

        Raises:
            RuntimeError: Instrument tells us if frequency has been set correctly.
            Otherwise RuntimeError.
        """
        write_str = ':{}:PWR:'.format(self.channel) + str(pwr) + 'dBm'
        read_str = self.ask(write_str)
        if read_str != 'Power Set':
            raise RuntimeError(
                         '{} is not \'Power Set\'. Setting power did not work'
                         .format(read_str))

    def _set_phase(self, ph:float) -> None:
        """Setting the phase in deg.

        Args:
            ph (float): phase angle in deg

        Raises:
            RuntimeError: Instrument tells us if phase has been set correctly.
            Otherwise RuntimeError.
        """
        write_str = ':{}:PHASE:'.format(self.channel) + str(float(ph)) + 'deg'
        read_str = self.ask(write_str)
        if read_str != 'Phase Set':
            raise RuntimeError(
                         '{} is not \'Phase Set\'. Setting phase did not work'
                         .format(read_str))

    def _get_temp(self) -> float:
        """Getting the temperature of a channel input/output in deg Celsius.
        Instrument returns string in the form 'Temp = 54C'

        Returns:
            float: Temperature in C, e.g. 54
        """
        raw_str = self.ask(':{}:TEMP?'.format(self.channel))
        T = raw_str.split(' ')[-1][:-1]
        return T


class HS900(VisaInstrument):
    """
    QCoDeS driver for the Holzworth HS9002B RF power source.
    It contains all parameters of the instrument.
    """
    def __init__(self, name: str, address: str, **kwargs) -> None:
        """
        Args:
            name: Name to use internally in QCoDeS
            address: VISA ressource address
        """
        super().__init__(name, address, terminator='\n', **kwargs)

        self.add_parameter(name='channel_names',
                           label='Channels',
                           get_parser=str,
                           get_cmd=self._get_channels) #No of ports

        self.add_parameter(name='ref_ext',
                           label='External Reference',
                           get_cmd=self._get_ext_ref,
                           set_cmd=self._set_ext_ref) # in Hz

        self.add_parameter(name='ref_int',
                           label='Internal Reference',
                           get_cmd=self._get_int_ref,
                           set_cmd=self._set_int_ref) # in Hz

        self.add_parameter(name='ref_PLL',
                           label='PLL Lock Status',
                           get_parser=str,
                           get_cmd=':REF:PLL?')


        model = self.IDN()['model']
        knownmodels = ['HS9001B', 'HS9002B', 'HS9003B', 'HS9004B',
                       'HS9005B', 'HS9006B', 'HS9007B', 'HS9008B']
        # Driver was only tested with 'HS9002B'.
        if model not in knownmodels:
            kmstring = ('{}, '*(len(knownmodels)-1)).format(*knownmodels[:-1])
            kmstring += 'and {}.'.format(knownmodels[-1])
            warnings.warn('Unknown model. Known models are: ' + kmstring)

        # Add the channel to the instrument
        channels = self.ask_raw(':ATTACH?').split(':')[2:-1]
        for ch_name in channels:
            channel = HS900Channel(self, ch_name, ch_name)
            self.add_submodule(ch_name, channel)

        self.connect_message()

    def _get_channels(self) -> list:
        """Getting the available channel names. Instrument returns string
        in the form :REF:CH1:CH2:'

        Returns:
            list: list with available channel names, e.g. ['CH1', 'CH2']
        """
        raw_str = self.ask(':ATTACH?')
        channels = raw_str.split(':')[2:-1]
        return channels

    def _get_int_ref(self) -> float:
        """
        Getting the internal reference frequency from the RF source channel
        in Hz. Instrument gives reference as a string in the format
        'Internal 100MHz'.

        Returns:
            float: frequency in Hz, e.g. 100e6
        """
        raw_str = self.ask(':REF:STATUS?')
        status = raw_str.split(' ')
        if status[0] == 'Internal':
            f_int_ref = float(status[1][:-3]) * 1e6
        else:
            f_int_ref = False
        return f_int_ref   

    def _set_int_ref(self, f_ref:{100e6}) -> None:
        """
        Function that sets internal reference

        Args:
            f_ref (float): accepts as argument 100e6

        Raises:
            RuntimeError: Function compares reply from instrument and raises
            RuntimeError if reference setting was not performed sucessfully
        """
        write_str = ':REF:INT:{}MHz'.format(str(int(f_ref / 1e6)))
        read_str = self.ask(write_str)
        if read_str != 'Reference Set to 100MHz Internal, PLL Disabled':
            raise RuntimeError(
                '{} is not \'Reference Set to {}MHz External, PLL Disabled\'. Setting reference did not work'
                               .format((read_str), str(int(f_ref / 1e6))))

    def _get_ext_ref(self) -> float:
        """
        Getting the internal reference frequency from the RF source channel
        in Hz. Instrument gives reference as a string in the format
        'Internal 100MHz'.

        Returns:
            float: frequency in Hz, e.g. 100e6
        """
        raw_str = self.ask(':REF:STATUS?')
        status = raw_str.split(' ')
        if status[0] == 'External':
            f_ext_ref = float(status[1][:-3]) * 1e6
        else:
            f_ext_ref = False
        return f_ext_ref  

    def _set_ext_ref(self, f_ref:{10e6, 100e6}) -> None:
        """
        Function that sets internal reference

        Args:
            f_ref (float): accepts as argument 100e6

        Raises:
            RuntimeError: Function compares reply from instrument and raises
            RuntimeError if reference setting was not performed sucessfully
        """
        write_str = ':REF:EXT:{}MHz'.format(str(int(f_ref / 1e6)))
        read_str = self.ask(write_str)
        if read_str != 'Reference Set to {}MHz External, PLL Enabled'.format(str(int(f_ref / 1e6))):
            raise RuntimeError(
                '{} is not \'Reference Set to {}MHz External, PLL Enabled\'. Setting reference did not work'
                               .format((read_str), str(int(f_ref / 1e6))))
