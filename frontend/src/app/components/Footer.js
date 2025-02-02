import Link from "next/link"
const Footer = () => {
    return (
        <>
            {/* FOOTER */}
            <div className=' max-h-10 bg-white flex gap-3 py-2 justify-center items-center border-t border-secondary '>
                ©2025
                <Link href={'https://techmahindra.com/'} target='_blank' className='hover:underline'>
                Tech Mahindra Limited
                </Link>
            </div>
        </>
    )
}

export default Footer;