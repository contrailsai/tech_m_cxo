import Image from 'next/image';

const Navbar = () => {

    return (
        <>
            {/* NAVBAR */}
            < div className='fixed z-50 top-0 bg-white  shadow flex items-center gap-10 w-full justify-start px-16 py-2' >
                <div className=' text-primary w-full text-xl font-bold flex justify-start items-center gap-3'>
                    <Image src={'/logo.svg'} width={30} height={20} alt="LOGO" />
                    Contrails AI
                </div>
            </div >

        </>
    )
}

export default Navbar;